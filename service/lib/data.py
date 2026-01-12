"""Data loading and routing table utilities."""

import pandas as pd
import ipaddress
import sys
from typing import Optional
from service.lib.radix_tree import RadixTree

""" Global params """
msk4 = int('f' * 8, 16)
msk6 = int('f' * 32, 16)
mxmetric = 0x8000

def get_df_pandas(filename: str) -> pd.DataFrame:
    """
    Load routing table from CSV file using pandas.
    
    This function reads a routing table file with semicolon-separated values
    and prepares it for LPM operations.

    Parameters
    ----------
    filename : str
        Path to the CSV file with ';' separator (format: prefix;next_hop)

    Returns
    -------
    pandas.DataFrame
        DataFrame with columns: prefix, next_hop, v, addr, prefixlen, metric
    """
    df = pd.read_csv(filename, sep=';', names=["prefix", "next_hop"])
    df['v'] = df["prefix"].map(lambda x: 6 if ':' in x else 4)
    df[['addr', 'prefixlen']] = df['prefix'].str.split('/', expand=True)
    df['prefixlen'] = df['prefixlen'].astype(int)
    df['metric'] = mxmetric
    return df


def get_df_polars(filename: str) -> pd.DataFrame:
    """
    Load routing table from CSV file.
    
    Note: Now uses pandas directly for simplicity. The name is kept for
    backward compatibility.

    Parameters
    ----------
    filename : str
        Path to the CSV file with ';' separator

    Returns
    -------
    pandas.DataFrame
        DataFrame with routing table data
    """
    return get_df_pandas(filename)

def prep_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare DataFrame by adding computed columns for LPM operations.
    
    Adds hexadecimal representations of addresses and masks, and converts
    next-hop addresses to integers for tie-breaking.

    Parameters
    ----------
    df : pandas.DataFrame
        Raw routing table dataframe

    Returns
    -------
    pandas.DataFrame
        Enhanced dataframe with addr, mask, and nhn columns
    """
    # IPv4
    df.loc[df['v'] == 4, 'nhn'] = df.loc[df['v'] == 4, 'next_hop'].map(
        lambda x: int(''.join([f'{int(i):02x}' for i in x.split('.')]), 16)
    )
    df.loc[df['v'] == 4, 'addr'] = df.loc[df['v'] == 4, 'addr'].map(
        lambda x: ''.join([f'{int(i):02x}' for i in x.split('.')])
    )
    df.loc[df['v'] == 4, 'mask'] = df.loc[df['v'] == 4, 'prefixlen'].map(
        lambda x: f'{(msk4 << (32 - x)) & msk4:08x}'
    )
    
    # IPv6
    df.loc[df['v'] == 6, 'nhn'] = df.loc[df['v'] == 6, 'next_hop'].map(
        lambda x: int(ipaddress.ip_network(x).network_address)
    ).astype('object')
    df.loc[df['v'] == 6, 'addr'] = df.loc[df['v'] == 6, 'addr'].map(
        lambda x: f'{int(ipaddress.ip_network(x).network_address):032x}'
    )
    df.loc[df['v'] == 6, 'mask'] = df.loc[df['v'] == 6, 'prefixlen'].map(
        lambda x: f'{(msk6 << (128 - x)) & msk6:032x}'
    )
    return df

def lpm_itr(df: pd.DataFrame, ipaddr: ipaddress.IPv4Network) -> pd.DataFrame:
    """
    Perform LPM using tuple iteration (legacy method).
    
    This is the slower O(n) approach, kept for compatibility.
    Consider using radix tree lookup instead.

    Parameters
    ----------
    df : pandas.DataFrame
        Routing table dataframe
    ipaddr : ipaddress.ip_network
        IP address to lookup

    Returns
    -------
    pandas.DataFrame
        Filtered dataframe with matching routes
    """
    ipad = ipaddr.network_address
    result = []
    for row in df.itertuples():
        if (int(row.mask, 16) & int(ipad) == int(row.addr, 16) and int(row.v) == ipad.version):
            result.append(row[0])
    return df.loc[result]

def lpm_map(df: pd.DataFrame, prefix: ipaddress.IPv4Network) -> pd.DataFrame:
    """
    Perform LPM using pandas map operations (legacy method).
    
    This is the O(n) linear scan approach, kept for compatibility.
    Consider using radix tree lookup instead for better performance.

    Parameters
    ----------
    df : pandas.DataFrame
        Routing table dataframe
    prefix : ipaddress.ip_network
        IP network/address to lookup

    Returns
    -------
    pandas.DataFrame
        Filtered dataframe with matching routes
    """
    ipadd = prefix.network_address
    int_ipadd = int(ipadd)
    if ipadd.version == 4:
        mas_ip = df.loc[df['v'] == 4, 'mask'].map(lambda x: f'{int(x, 16) & int_ipadd:08x}')
        mask = df.loc[df['v'] == 4, 'addr'] == mas_ip
    else:
        mas_ip = df.loc[df['v'] == 6, 'mask'].map(lambda x: f'{int(x, 16) & int_ipadd:032x}')
        mask = df.loc[df['v'] == 6, 'addr'] == mas_ip
    return df.loc[mask.loc[mask].index]


def build_radix_tree(df: pd.DataFrame) -> RadixTree:
    """
    Build a radix tree from the routing table DataFrame.
    
    This provides O(prefix_length) lookup complexity instead of O(n).
    
    Parameters
    ----------
    df : pandas.DataFrame
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
    
    # Use itertuples for faster iteration
    for idx, row in enumerate(df.itertuples(), 1):
        tree.insert(
            prefix=row.prefix,
            next_hop=row.next_hop,
            metric=row.metric
        )
        
        # Progress indicator every 100k routes
        if idx % 100000 == 0:
            print(f"  Processed {idx:,}/{total:,} routes ({idx*100//total}%)", 
                  file=sys.stderr, flush=True)
    
    print(f"✅ Radix tree built: {tree.route_count:,} routes loaded", 
          file=sys.stderr, flush=True)
    
    return tree


def lpm_lookup_radix(tree: RadixTree, ip_address: str) -> pd.DataFrame:
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
    pandas.DataFrame
        DataFrame with matching routes
    """
    try:
        addr = ipaddress.ip_address(ip_address)
    except (ValueError, ipaddress.AddressValueError):
        return pd.DataFrame()
    
    # Get all matching routes from radix tree
    routes = tree.lookup(str(addr))
    
    if not routes:
        return pd.DataFrame()
    
    # Convert to DataFrame format compatible with existing code
    data = {
        'prefix': [r.prefix for r in routes],
        'next_hop': [r.next_hop for r in routes],
        'metric': [r.metric for r in routes],
        'prefixlen': [r.prefix_len for r in routes],
        'nhn': [r.nhn for r in routes],
        'v': [r.version for r in routes]
    }
    
    return pd.DataFrame(data)


if __name__ == '__main__':
    pass