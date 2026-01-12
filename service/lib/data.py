"""Data loading and routing table utilities."""

import polars as pl
import ipaddress
import sys
from service.lib.radix_tree import RadixTree

""" Global params """
msk4 = int('f' * 8, 16)
msk6 = int('f' * 32, 16)
mxmetric = 0x8000


def get_df_polars(filename: str) -> pl.DataFrame:
    """
    Load routing table from CSV file using polars.

    Parameters
    ----------
    filename : str
        Path to the CSV file with ';' separator (format: prefix;next_hop)

    Returns
    -------
    polars.DataFrame
        DataFrame with columns: prefix, next_hop, v, addr, prefixlen, metric
    """
    df = pl.read_csv(
        filename,
        separator=';',
        has_header=False,
        new_columns=["prefix", "next_hop"]
    )
    
    # Add version column (4 for IPv4, 6 for IPv6)
    df = df.with_columns([
        pl.when(pl.col("prefix").str.contains(":"))
          .then(pl.lit(6))
          .otherwise(pl.lit(4))
          .alias("v")
    ])
    
    # Split prefix into addr and prefixlen
    df = df.with_columns([
        pl.col("prefix").str.split("/").list.get(0).alias("addr"),
        pl.col("prefix").str.split("/").list.get(1).cast(pl.Int32).alias("prefixlen"),
        pl.lit(mxmetric).alias("metric")
    ])
    
    return df

def prep_df(df: pl.DataFrame) -> pl.DataFrame:
    """
    Prepare DataFrame by adding computed columns for LPM operations.
    
    Adds hexadecimal representations of addresses and masks, and converts
    next-hop addresses to integers for tie-breaking.

    Parameters
    ----------
    df : polars.DataFrame
        Raw routing table dataframe

    Returns
    -------
    polars.DataFrame
        Enhanced dataframe with addr, mask, and nhn columns
    """
    # Helper function to convert IPv4 to hex
    def ipv4_to_hex(ip: str) -> str:
        parts = ip.split('.')
        return ''.join([f'{int(p):02x}' for p in parts])
    
    # Helper function to convert IPv4 to integer
    def ipv4_to_int(ip: str) -> int:
        parts = ip.split('.')
        return int(''.join([f'{int(p):02x}' for p in parts]), 16)
    
    # Helper function for IPv4 mask
    def ipv4_mask(prefixlen: int) -> str:
        return f'{(msk4 << (32 - prefixlen)) & msk4:08x}'
    
    # Helper function for IPv6 mask
    def ipv6_mask(prefixlen: int) -> str:
        return f'{(msk6 << (128 - prefixlen)) & msk6:032x}'
    
    # Process IPv4 routes
    ipv4_df = df.filter(pl.col("v") == 4)
    if len(ipv4_df) > 0:
        ipv4_df = ipv4_df.with_columns([
            pl.col("next_hop").map_elements(lambda x: str(ipv4_to_int(x)), return_dtype=pl.Utf8).alias("nhn"),
            pl.col("addr").map_elements(ipv4_to_hex, return_dtype=pl.Utf8).alias("addr"),
            pl.col("prefixlen").map_elements(ipv4_mask, return_dtype=pl.Utf8).alias("mask")
        ])
    
    # Process IPv6 routes
    ipv6_df = df.filter(pl.col("v") == 6)
    if len(ipv6_df) > 0:
        # IPv6 addresses as integers exceed Int64 - use string representation
        ipv6_df = ipv6_df.with_columns([
            pl.col("next_hop").map_elements(
                lambda x: str(int(ipaddress.ip_network(x).network_address)),
                return_dtype=pl.Utf8
            ).alias("nhn"),
            pl.col("addr").map_elements(
                lambda x: f'{int(ipaddress.ip_network(x).network_address):032x}',
                return_dtype=pl.Utf8
            ).alias("addr"),
            pl.col("prefixlen").map_elements(ipv6_mask, return_dtype=pl.Utf8).alias("mask")
        ])
    
    # Combine back together
    if len(ipv4_df) > 0 and len(ipv6_df) > 0:
        result = pl.concat([ipv4_df, ipv6_df])
    elif len(ipv4_df) > 0:
        result = ipv4_df
    else:
        result = ipv6_df
    
    return result


def lpm_map(df: pl.DataFrame, prefix: ipaddress.IPv4Network) -> pl.DataFrame:
    """
    Perform LPM using polars operations (legacy method).
    
    This is the O(n) linear scan approach, kept for compatibility.
    Consider using radix tree lookup instead for better performance.

    Parameters
    ----------
    df : polars.DataFrame
        Routing table dataframe
    prefix : ipaddress.ip_network
        IP network/address to lookup

    Returns
    -------
    polars.DataFrame
        Filtered dataframe with matching routes
    """
    ipadd = prefix.network_address
    int_ipadd = int(ipadd)
    version = ipadd.version
    
    # Filter by IP version and apply mask matching
    if version == 4:
        filtered = df.filter(pl.col('v') == 4).with_columns([
            pl.col('mask').map_elements(
                lambda x: f'{int(x, 16) & int_ipadd:08x}',
                return_dtype=pl.Utf8
            ).alias('masked_ip')
        ])
        result = filtered.filter(pl.col('addr') == pl.col('masked_ip'))
    else:
        filtered = df.filter(pl.col('v') == 6).with_columns([
            pl.col('mask').map_elements(
                lambda x: f'{int(x, 16) & int_ipadd:032x}',
                return_dtype=pl.Utf8
            ).alias('masked_ip')
        ])
        result = filtered.filter(pl.col('addr') == pl.col('masked_ip'))
    
    return result.drop('masked_ip') if 'masked_ip' in result.columns else result


def build_radix_tree(df: pl.DataFrame) -> RadixTree:
    """
    Build a radix tree from the routing table DataFrame.
    
    This provides O(prefix_length) lookup complexity instead of O(n).
    
    Parameters
    ----------
    df : polars.DataFrame
        The routing table dataframe with columns: prefix, next_hop, metric
    
    Returns
    -------
    RadixTree
        A radix tree containing all routes
    """
    import sys
    tree = RadixTree()
    total = len(df)
    
    print(f"Building radix tree from {total:,} routes...", file=sys.stderr, flush=True)
    
    # Iterate through rows
    for idx, row in enumerate(df.iter_rows(named=True), 1):
        tree.insert(
            prefix=row['prefix'],
            next_hop=row['next_hop'],
            metric=row['metric']
        )
        
        # Progress indicator every 100k routes
        if idx % 100000 == 0:
            print(f"  Processed {idx:,}/{total:,} routes ({idx*100//total}%)", 
                  file=sys.stderr, flush=True)
    
    print(f"✅ Radix tree built: {tree.route_count:,} routes loaded", 
          file=sys.stderr, flush=True)
    
    return tree


def lpm_lookup_radix(tree: RadixTree, ip_address: str) -> pl.DataFrame:
    """
    Perform LPM lookup using radix tree.
    
    This is significantly faster than lpm_map for large routing tables.
    Returns a DataFrame compatible with existing code.
    
    Parameters
    ----------
    tree : RadixTree
        The radix tree containing routes
    ip_address : str
        IP address to lookup
    
    Returns
    -------
    polars.DataFrame
        DataFrame with matching routes
    """
    try:
        addr = ipaddress.ip_address(ip_address)
    except (ValueError, ipaddress.AddressValueError):
        return pl.DataFrame()
    
    # Get all matching routes from radix tree
    routes = tree.lookup(str(addr))
    
    if not routes:
        return pl.DataFrame()
    
    # Convert to DataFrame format compatible with existing code
    data = {
        'prefix': [r.prefix for r in routes],
        'next_hop': [r.next_hop for r in routes],
        'metric': [r.metric for r in routes],
        'prefixlen': [r.prefix_len for r in routes],
        'nhn': [r.nhn for r in routes],
        'v': [r.version for r in routes]
    }
    
    return pl.DataFrame(data)


if __name__ == '__main__':
    pass