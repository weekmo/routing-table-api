import polars as pl
import ipaddress as ia
from time import time

from service.utils.data import get_df_polars

def get_df(filename):
    msk4 = int('f' * 8,16)
    msk6 = int('f' * 32,16)
    mxmetric = 0x8000
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
        ).collect().to_pandas()
    
    """ IPv4 """
    df.loc[df['v']==4,'nhn'] = df.loc[df['v']==4,'next_hop'].map(lambda x: int(''.join([f'{int(i):02x}' for i in x.split('.')]),16))
    df.loc[df['v']==4,'addr'] = df.loc[df['v']==4,'addr'].map(lambda x: ''.join([f'{int(i):02x}' for i in x.split('.')]))
    df.loc[df['v']==4,'mask'] = df.loc[df['v']==4,'prefixlen'].map(lambda x: f'{(msk4 << (32 - x)) & msk4:08x}')
    df.loc[df['v']==4,'nhn'] -= df.loc[df['v']==4,'nhn'].min()
    
    """ IPv6 """
    df.loc[df['v']==6,'nhn'] = df.loc[df['v']==6,'next_hop'].map(lambda x : int(ia.ip_network(x).network_address))
    df.loc[df['v']==6,'addr'] = df.loc[df['v']==6,'addr'].map(lambda x : f'{int(ia.ip_network(x).network_address):032x}')
    df.loc[df['v']==6,'mask'] = df.loc[df['v']==6,'prefixlen'].map(lambda x: f'{(msk6 << (128 - x)) & msk6:032x}')
    df.loc[df['v']==6,'nhn'] -= df.loc[df['v']==6,'nhn'].min()
    return df

def lpm_map(df,prefix):
    df = pl.from_pandas(df)
    ipadd = prefix.network_address
    int_ipadd = int(ipadd)
    version = ipadd.version
    mask_hex_len = f'%0{1 << (version-1)}x'
    sub = df.filter([
        (pl.col('v') == version),
        (int(pl.col('mask').str,16))
    ])
    mas_ip = df.loc[df['v']==version,'mask'].map(lambda x : mask_hex_len % (int(x,16) & int_ipadd))
    mask = df.loc[df['v']==version,'addr'] == mas_ip

    return df.loc[mask.loc[mask].index]

if __name__ == '__main__':
    file_name = 'routes.txt'
    df = get_df(file_name)
    """
    end = 0
    for _ in range(10):
        start = time()
        get_df2(file_name)
        end += time() - start
    print("With PL",end/10)

    end = 0
    for _ in range(10):
        start = time()
        end += time() - start
    print("Pure Pandas",end/10)
    """

