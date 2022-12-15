import numpy as np
import pandas as pd
import polars as pl
import ipaddress
from concurrent.futures import ProcessPoolExecutor


""" Global params """
msk4 = int('f' * 8,16)
msk6 = int('f' * 32,16)
mxmetric = 0x8000

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
    return df.to_pandas()

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
    df.loc[df['v']==4,'nhn'] = df.loc[df['v']==4,'next_hop'].map(lambda x: int(''.join([f'{int(i):02x}' for i in x.split('.')]),16))
    df.loc[df['v']==4,'addr'] = df.loc[df['v']==4,'addr'].map(lambda x: ''.join([f'{int(i):02x}' for i in x.split('.')]))
    df.loc[df['v']==4,'mask'] = df.loc[df['v']==4,'prefixlen'].map(lambda x: f'{(msk4 << (32 - x)) & msk4:08x}')
    df.loc[df['v']==4,'nhn'] -= df.loc[df['v']==4,'nhn'].min()
    
    #""" IPv6 """
    df.loc[df['v']==6,'nhn'] = df.loc[df['v']==6,'next_hop'].map(lambda x : int(ipaddress.ip_network(x).network_address))
    df.loc[df['v']==6,'addr'] = df.loc[df['v']==6,'addr'].map(lambda x : f'{int(ipaddress.ip_network(x).network_address):032x}')
    df.loc[df['v']==6,'mask'] = df.loc[df['v']==6,'prefixlen'].map(lambda x: f'{(msk6 << (128 - x)) & msk6:032x}')
    df.loc[df['v']==6,'nhn'] -= df.loc[df['v']==6,'nhn'].min()
    return df

df = get_df_polars('routes.txt')

sub_dataframes = np.array_split(df,4)


if __name__ == "__name__":
    with ProcessPoolExecutor() as exec:
        for res in exec.map(prep_df, sub_dataframes):
            print(res)

