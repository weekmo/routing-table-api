import pandas as pd
import ipaddress
import polars as pl

msk4 = int('f' * 8,16)
msk6 = int('f' * 32,16)
mxmetric = 0x8000

def get_df_pandas(filename):
    df = pd.read_csv(filename, sep=';', names=["prefix","next_hop"])
    df['v'] = df["prefix"].map(lambda x : 6 if ':' in x else 4)
    df[['addr','prefixlen']] = df['prefix'].str.split('/',expand=True)
    df['prefixlen'] = df['prefixlen'].astype(int)
    df['metric'] = mxmetric
    return df

def get_df_polars(filename):
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
    return df.collect().to_pandas()

def prep_df(df):
    """ IPv4 """
    df.loc[df['v']==4,'nhn'] = df.loc[df['v']==4,'next_hop'].map(lambda x: int(''.join([f'{int(i):02x}' for i in x.split('.')]),16))
    df.loc[df['v']==4,'addr'] = df.loc[df['v']==4,'addr'].map(lambda x: ''.join([f'{int(i):02x}' for i in x.split('.')]))
    df.loc[df['v']==4,'mask'] = df.loc[df['v']==4,'prefixlen'].map(lambda x: f'{(msk4 << (32 - x)) & msk4:08x}')
    df.loc[df['v']==4,'nhn'] -= df.loc[df['v']==4,'nhn'].min()
    
    """ IPv6 """
    df.loc[df['v']==6,'nhn'] = df.loc[df['v']==6,'next_hop'].map(lambda x : int(ipaddress.ip_network(x).network_address))
    df.loc[df['v']==6,'addr'] = df.loc[df['v']==6,'addr'].map(lambda x : f'{int(ipaddress.ip_network(x).network_address):032x}')
    df.loc[df['v']==6,'mask'] = df.loc[df['v']==6,'prefixlen'].map(lambda x: f'{(msk6 << (128 - x)) & msk6:032x}')
    df.loc[df['v']==6,'nhn'] -= df.loc[df['v']==6,'nhn'].min()
    return df

async def lpm_itr(df, ipaddr):
    ipad = ipaddr.network_address
    result = []
    for row in df.itertuples():
        if(int(row.mask,16) & int(ipad) == int(row.addr,16) and int(row.v) == ipad.version):
            result.append(row[0])
    return df.loc[result]

async def lpm_map(df,prefix):
    ipadd = prefix.network_address
    int_ipadd = int(ipadd)
    if ipadd.version == 4:
        mas_ip = df.loc[df['v']==4,'mask'].map(lambda x : f'{int(x,16) & int_ipadd:08x}')
        mask = df.loc[df['v']==4,'addr'] == mas_ip
    else:
        mas_ip = df.loc[df['v']==6,'mask'].map(lambda x : f'{int(x,16) & int_ipadd:032x}')
        mask = df.loc[df['v']==6,'addr'] == mas_ip
    return df.loc[mask.loc[mask].index]
if __name__ == '__main__':
    pass