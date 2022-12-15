import pandas as pd
import ipaddress
import polars as pl
from multiprocessing import Pool
import numpy as np

""" Global params """
msk4 = int('f' * 8,16)
msk6 = int('f' * 32,16)
mxmetric = 0x8000

def get_df_pandas(filename):
    """
    This function is created specifically for this app, it might need to be refined for different use cases.
    It takes a file name as a text and return pandas dataframe using pandas

    Parameters
    ----------
    filename : str
        the file name should be read, it sould be csv file with ';' separator

    Returns
    -------
    pandas.DataFrame
        it returns dataframe with specific columns
    """
    df = pd.read_csv(filename, sep=';', names=["prefix","next_hop"])
    df['v'] = df["prefix"].map(lambda x : 6 if ':' in x else 4)
    df[['addr','prefixlen']] = df['prefix'].str.split('/',expand=True)
    df['prefixlen'] = df['prefixlen'].astype(int)
    df['metric'] = mxmetric
    return prep_df(df)

def get_df_polars(filename):
    """
    This function is created specifically for this app, it might need to be refined for different use cases.
    It takes a file name as a text and return pandas dataframe using polars

    Parameters
    ----------
    filename : str
        the file name should be read, it sould be csv file with ';' separator

    Returns
    -------
    pandas.DataFrame
        it returns dataframe with specific columns
    """
    df = pl.read_csv(filename, sep=';', has_header=False, new_columns=['prefix','next_hop']).lazy()
    df = df.with_columns([
            pl.lit(mxmetric).cast(pl.UInt16).alias('metric'),
            pl.col('prefix').str.split('/').alias('div')
        ]).with_column(
            pl.struct([
                    pl.col('div').arr.get(0).alias('addr'),
                    pl.col('div').arr.get(1).cast(pl.UInt8).alias('prefixlen'),
            ]).alias('div'),
        ).unnest('div').with_columns(
            pl.when(pl.col('addr').str.contains(':')).then(6).otherwise(4).cast(pl.UInt8).alias('v')
        )
    df = df.collect()
    return prep_df(df.to_pandas())

def prep_df(df):
    """
    This function is created specifically for this app, it might need to be refined for different use cases.
    It takes pandas.DataFrame, add more features and return it back

    Parameters
    ----------
    df : pandas.DataFrame
        the param sould be pandas.DataFrame

    Returns
    -------
    pandas.DataFrame
        it returns dataframe with specific columns
    """
    #""" IPv4 """
    df.loc[df['v']==4,'nhn'] = df.loc[df['v']==4]['next_hop'].map(lambda x: int(''.join([f'{int(i):02x}' for i in x.split('.')]),16))
    df.loc[df['v']==4,'addr'] = df.loc[df['v']==4,'addr'].map(lambda x: ''.join([f'{int(i):02x}' for i in x.split('.')]))
    df.loc[df['v']==4,'mask'] = df.loc[df['v']==4,'prefixlen'].map(lambda x: f'{(msk4 << (32 - x)) & msk4:08x}')
    df.loc[df['v']==4,'nhn'] -= df.loc[df['v']==4,'nhn'].min()
    
    #""" IPv6 """
    df.loc[df['v']==6,'nhn'] = df.loc[df['v']==6,'next_hop'].map(lambda x : int(ipaddress.ip_network(x).network_address))
    df.loc[df['v']==6,'addr'] = df.loc[df['v']==6,'addr'].map(lambda x : f'{int(ipaddress.ip_network(x).network_address):032x}')
    df.loc[df['v']==6,'mask'] = df.loc[df['v']==6,'prefixlen'].map(lambda x: f'{(msk6 << (128 - x)) & msk6:032x}')
    df.loc[df['v']==6,'nhn'] -= df.loc[df['v']==6,'nhn'].min()
    return df

async def lpm_itr(df, ipaddr):
    """
    This function is created specifically for this app, it might need to be refined for different use cases.
    It takes df as DataFrame and ipaddr as IP address for searching the next hop for the IP address,
    it uses tuple iteration

    Parameters
    ----------
    df : pandas.DataFrame
        the param sould be pandas.DataFrame

    ipaddr : ipaddress.ip_network
        the param sould be pandas.DataFrame

    Returns
    -------
    pandas.DataFrame
        it returns filterd dataframe with required values or empty
    """
    ipad = ipaddr.network_address
    result = []
    for row in df.itertuples():
        if(int(row.mask,16) & int(ipad) == int(row.addr,16) and int(row.v) == ipad.version):
            result.append(row[0])
    return df.loc[result]

async def lpm_map(df,prefix):
    """
    This function is created specifically for this app, it might need to be refined for different use cases.
    It takes df as DataFrame and ipaddr as IP address for searching the next hop for the IP address,
    it uses map from series to find the next hop

    Parameters
    ----------
    df : pandas.DataFrame
        the param sould be pandas.DataFrame

    ipaddr : ipaddress.ip_network
        the param sould be pandas.DataFrame

    Returns
    -------
    pandas.DataFrame
        it returns filterd dataframe with required values or empty
    """

    ipadd = prefix.network_address
    int_ipadd = int(ipadd)
    version = ipadd.version
    mask_hex_len = f'%0{1 << (version-1)}x'

    mas_ip = df.loc[df['v']==version,'mask'].map(lambda x : mask_hex_len % (int(x,16) & int_ipadd))
    mask = df.loc[df['v']==version,'addr'] == mas_ip

    return df.loc[mask.loc[mask].index]

async def lpm_update(df, prefix_ip,nh,metric,matchd="orlonger"):
    """
    This function is created specifically for this app, it might need to be refined for different use cases.
    It searches and updates route(s) according to the params provided. It return sub-dataframe for error handling.

    Parameters
    ----------
    df : pandas.DataFrame
        the param sould be pandas.DataFrame which needs to be updated

    prefix_ip : ipaddress.ip_network
        the param sould be an object of ipaddress.ip_network (IP), it is the prefix
    
    nh : str
        the param sould be IP adress in string format, it is the next hop

    metric : int
        the param sould be the metric value that needs to be updated in int format

    matchd : str = orlonger [orlonger, exact]
        the param sould the method for serching the routbe the metric value that needs to be updated in int format

    Returns
    -------
    pandas.DataFrame
        it returns filterd dataframe with required values or empty
    """

    if matchd == "exact":
        next_hop_df = df.loc[(df['next_hop'] == nh) & (df['prefix'] == prefix_ip.with_prefixlen)]
    else:
        next_hop_df = await lpm_map(df, prefix_ip)
        next_hop_df = next_hop_df.loc[(next_hop_df['next_hop'] == nh) & (next_hop_df['prefixlen'] !=0)]
    next_hop_df['metric'] = metric
    return next_hop_df

if __name__ == '__main__':
    pass