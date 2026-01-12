"""Data processing utilities for routing table operations."""

from multiprocessing import Pool
import ipaddress

import numpy as np
import pandas as pd
import polars as pl

# Global constants
MSK4 = int("f" * 8, 16)  # IPv4 mask (0xffffffff)
MSK6 = int("f" * 32, 16)  # IPv6 mask
MAX_METRIC = 0x8000  # Default maximum metric


def get_df_pandas(filename: str, proc_num: int) -> pd.DataFrame:
    """
    Load and process routing table from CSV file using pandas.
    
    This function reads a routing table CSV file and processes it for efficient
    longest prefix matching operations.
    
    Args:
        filename: Path to CSV file with format: prefix;next_hop
        proc_num: Number of parallel processes for data preparation
    
    Returns:
        Processed pandas DataFrame with routing table data
        
    Raises:
        FileNotFoundError: If the routing file doesn't exist
        ValueError: If the file format is invalid
    """
    df = pd.read_csv(filename, sep=";", names=["prefix", "next_hop"])
    df["v"] = df["prefix"].map(lambda x: 6 if ":" in x else 4)
    df[["addr", "prefixlen"]] = df["prefix"].str.split("/", expand=True)
    df["prefixlen"] = df["prefixlen"].astype(int)
    df["metric"] = MAX_METRIC
    return __multi_process_prep_df(df, proc_num)


def get_df_polars(filename: str, proc_num: int) -> pd.DataFrame:
    """
    Load and process routing table from CSV file using polars (faster).
    
    This function uses Polars for efficient CSV parsing, then converts to pandas
    for compatibility with existing LPM functions.
    
    Args:
        filename: Path to CSV file with format: prefix;next_hop
        proc_num: Number of parallel processes for data preparation
    
    Returns:
        Processed pandas DataFrame with routing table data
        
    Raises:
        FileNotFoundError: If the routing file doesn't exist
        ValueError: If the file format is invalid
    """
    df = (
        pl.read_csv(filename, separator=";", has_header=False, new_columns=["prefix", "next_hop"])
        .lazy()
        .with_columns(
            [
                pl.lit(MAX_METRIC).cast(pl.UInt16).alias("metric"),
                pl.col("prefix").str.split("/").alias("div"),
            ]
        )
        .with_columns(
            pl.struct(
                [
                    pl.col("div").list.get(0).alias("addr"),
                    pl.col("div").list.get(1).cast(pl.UInt8).alias("prefixlen"),
                ]
            ).alias("div")
        )
        .unnest("div")
        .with_columns(
            pl.when(pl.col("addr").str.contains(":"))
            .then(pl.lit(6))
            .otherwise(pl.lit(4))
            .cast(pl.UInt8)
            .alias("v")
        )
        .collect()
        .to_pandas()
    )
    return __multi_process_prep_df(df, proc_num)


def __multi_process_prep_df(df: pd.DataFrame, proc_num: int) -> pd.DataFrame:
    """
    Split DataFrame and process in parallel using multiprocessing.
    
    Args:
        df: DataFrame to process
        proc_num: Number of parallel processes
        
    Returns:
        Concatenated processed DataFrame
    """
    sub_frames = np.array_split(df, proc_num)
    with Pool(proc_num) as pool:
        result = pool.map(__prep_df, sub_frames)
    return pd.concat(result)


def __prep_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare DataFrame by converting IP addresses to hex format for fast matching.
    
    This function processes both IPv4 and IPv6 addresses, converting them to
    hexadecimal representation for efficient bitwise operations during LPM.
    
    Args:
        df: DataFrame with raw routing data
        
    Returns:
        DataFrame with hex-encoded addresses and masks
    """
    # Process IPv4 routes
    v4_mask = df["v"] == 4
    if v4_mask.any():
        df.loc[v4_mask, "nhn"] = df.loc[v4_mask, "next_hop"].map(
            lambda x: int("".join([f"{int(i):02x}" for i in x.split(".")]), 16)
        )
        df.loc[v4_mask, "addr"] = df.loc[v4_mask, "addr"].map(
            lambda x: "".join([f"{int(i):02x}" for i in x.split(".")])
        )
        df.loc[v4_mask, "mask"] = df.loc[v4_mask, "prefixlen"].map(
            lambda x: f"{(MSK4 << (32 - x)) & MSK4:08x}"
        )
        # Normalize next hop numbers
        if df.loc[v4_mask, "nhn"].notna().any():
            df.loc[v4_mask, "nhn"] -= df.loc[v4_mask, "nhn"].min()

    # Process IPv6 routes
    v6_mask = df["v"] == 6
    if v6_mask.any():
        df.loc[v6_mask, "nhn"] = df.loc[v6_mask, "next_hop"].map(
            lambda x: int(ipaddress.ip_network(x).network_address)
        )
        df.loc[v6_mask, "addr"] = df.loc[v6_mask, "addr"].map(
            lambda x: f"{int(ipaddress.ip_network(x).network_address):032x}"
        )
        df.loc[v6_mask, "mask"] = df.loc[v6_mask, "prefixlen"].map(
            lambda x: f"{(MSK6 << (128 - x)) & MSK6:032x}"
        )
        # Normalize next hop numbers
        if df.loc[v6_mask, "nhn"].notna().any():
            df.loc[v6_mask, "nhn"] -= df.loc[v6_mask, "nhn"].min()

    return df


def lpm_map(df: pd.DataFrame, prefix: ipaddress.IPv4Network | ipaddress.IPv6Network) -> pd.DataFrame:
    """
    Perform longest prefix match (LPM) lookup using vectorized operations.
    
    This is an optimized LPM implementation using pandas Series.map() for
    better performance compared to iterative approaches.
    
    Args:
        df: Routing table DataFrame
        prefix: IP network to lookup
        
    Returns:
        DataFrame containing all matching routes (may be empty)
    """
    ipadd = prefix.network_address
    int_ipadd = int(ipadd)
    version = ipadd.version
    mask_hex_len = f"%0{1 << (version - 1)}x"

    # Filter by IP version and perform bitwise mask matching
    version_mask = df["v"] == version
    masked_ips = df.loc[version_mask, "mask"].map(
        lambda x: mask_hex_len % (int(x, 16) & int_ipadd)
    )
    addr_match = df.loc[version_mask, "addr"] == masked_ips

    return df.loc[addr_match.loc[addr_match].index]


def lpm_update(
    df: pd.DataFrame,
    prefix_ip: ipaddress.IPv4Network | ipaddress.IPv6Network,
    nh: str,
    metric: int,
    matchd: str = "orlonger",
) -> pd.DataFrame:
    """
    Search and update routes matching specified criteria.
    
    Args:
        df: Routing table DataFrame to search
        prefix_ip: IP network prefix to match
        nh: Next hop IP address (as string)
        metric: New metric value to set
        matchd: Match type - "exact" or "orlonger" (default)
        
    Returns:
        DataFrame with updated routes (may be empty if no matches)
    """
    if matchd == "exact":
        # Exact match: both prefix and next hop must match exactly
        next_hop_df = df.loc[
            (df["next_hop"] == nh) & (df["prefix"] == prefix_ip.with_prefixlen)
        ].copy()
    else:
        # Or-longer match: find all routes within the prefix that use this next hop
        next_hop_df = lpm_map(df, prefix_ip)
        next_hop_df = next_hop_df.loc[
            (next_hop_df["next_hop"] == nh) & (next_hop_df["prefixlen"] != 0)
        ].copy()

    next_hop_df["metric"] = metric
    return next_hop_df


def lpm_itr(df: pd.DataFrame, ipaddr: ipaddress.IPv4Network | ipaddress.IPv6Network) -> pd.DataFrame:
    """
    Perform LPM lookup using tuple iteration (slower, kept for reference).
    
    This is a reference implementation using row iteration. The lpm_map function
    is preferred for better performance.
    
    Args:
        df: Routing table DataFrame
        ipaddr: IP network to lookup
        
    Returns:
        DataFrame containing all matching routes
    """
    ipad = ipaddr.network_address
    result = []
    for row in df.itertuples():
        if int(row.mask, 16) & int(ipad) == int(row.addr, 16) and int(row.v) == ipad.version:
            result.append(row[0])
    return df.loc[result]


if __name__ == "__main__":
    pass