import polars as pl
import ipaddress as ia
from time import time

def get_df(filename):
    def app(x):
        ip = ia.ip_network(x)
        return [f'{int(ip.network_address):0x}',f'{int(ip.netmask):0x}', str(ip.prefixlen), str(ip.version)]

    df = pl.read_csv(filename, sep=';', has_header=False, new_columns=['prefix','next_hop']).lazy()

    df = df.with_columns([
        pl.lit(0x8000).cast(pl.UInt16).alias('metric'),
        pl.col('prefix').apply(lambda x : app(x)).alias('div'),
        pl.col('next_hop').apply(lambda x : app(x)[0]).alias('nhn')
    ])

    df = df.with_column(
            pl.struct([
                pl.col('div').arr.get(0).alias('addr'),
                pl.col('div').arr.get(1).alias('mask'),
                pl.col('div').arr.get(2).cast(pl.UInt8).alias('prefixlen'),
                pl.col('div').arr.get(3).cast(pl.UInt8).alias('v'),
            ]).alias('div'),
    ).unnest('div')

    dfv4 = df.filter(
        (pl.col('v') == 4)
    )

    dfv6 = df.filter(
        (pl.col('v') == 6)
    )
    return dfv4

if __name__ == '__main__':
    
    df = get_df('routes_sample.txt')
    print(df.fetch(8))
    #print(df.fetch(8))
"""
end = 0
for _ in range(10):
    start = time()
    get_df('routes.txt')
    end += time() - start
print(end/10)
"""

"""
out = df.select([
    pl.col('prefix'),
    pl.col('addr').apply(lambda x : ia.ip_network(int(x,16)).network_address).alias('back_addr'),
    pl.col('mask'),
    pl.col('mask').apply(lambda x : ia.ip_network(int(x,16)).network_address).alias('back_mask'),
    pl.col('next_hop'),
    pl.col('nhn').apply(lambda x : ia.ip_network(int(x,16)).network_address).alias('back_nhn')
])

print(out.fetch(8))
"""