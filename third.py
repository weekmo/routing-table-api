import polars as pl
import ipaddress as ia
from time import time

from service.utils.data import get_df as gf

def get_df(file_name):
    msk4 = int('f' * 8,16)
    msk6 = int('f' * 32,16)


    df = pl.read_csv(file_name, sep=';', has_header=False, new_columns=['prefix','next_hop']).lazy()

    df = df.with_columns([
            pl.lit(0x8000).cast(pl.UInt16).alias('metric'),
            pl.col('prefix').str.split('/').alias('div')
        ]).with_column(
            pl.struct([
                    pl.col('div').arr.get(0).alias('addr'),
                    pl.col('div').arr.get(1).cast(pl.UInt8).alias('prefixlen'),
            ]).alias('div'),
        ).unnest('div').with_columns(
            pl.when(pl.col('addr').str.contains(':')).then(6).otherwise(4).cast(pl.UInt8).alias('v')
        )

    dfv4,dfv6 = df.collect().partition_by(groups='v')

    dfv4 = dfv4.lazy().with_columns([
        pl.col('addr').str.split('.').arr.eval(pl.element().cast(pl.UInt8)),
        pl.col('next_hop').str.split('.').arr.eval(pl.element().cast(pl.UInt8)).alias('nhn')
    ]).collect().to_pandas()

    dfv6 = dfv6.to_pandas()
    """ IPv4 """
    dfv4['nhn'] = dfv4['nhn'].map(lambda x: int(''.join([f'{i:02x}' for i in x]),16))
    dfv4['addr'] = dfv4['addr'].map(lambda x: ''.join([f'{i:02x}' for i in x]))
    dfv4['mask'] = dfv4['prefixlen'].map(lambda x: f'{(msk4 << (32 - x)) & msk4:08x}')
    dfv4['nhn'] -= dfv4['nhn'].min()

    """ IPv6 """
    dfv6['nhn'] = dfv6['next_hop'].map(lambda x : int(ia.ip_network(x).network_address))
    dfv6['addr'] = dfv6['addr'].map(lambda x : f'{int(ia.ip_network(x).network_address):032x}')
    dfv6['mask'] = dfv6['prefixlen'].map(lambda x: f'{(msk6 << (128 - x)) & msk6:032x}')
    dfv6['nhn'] -= dfv6['nhn'].min()

    return pl.concat([pl.from_pandas(dfv4),pl.from_pandas(dfv6)],how='vertical')

def get_df2(filename):
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

if __name__ == '__main__':
    file_name = 'routes.txt'
    df = get_df2(file_name)
    df = gf(file_name)
    
    end = 0
    for _ in range(10):
        start = time()
        get_df2(file_name)
        end += time() - start
    print("With PL",end/10)

    end = 0
    for _ in range(10):
        start = time()
        gf(file_name)
        end += time() - start
    print("Pure Pandas",end/10)
    

