
import ipaddress
import pandas as pd
import numpy as np
from time import time

import multiprocessing as mp

def meth1(filename):
    #9.383077692985534
    """
    def iptohex(ip):
        return ''.join([f'{int(i):02x}' for i in ip.split('.')])
    """
    msk4 = int('f' * 8,16)
    msk6 = int('f' * 32,16)

    #print(msk4)
    #print(msk6)

    df = pd.read_csv(filename, sep=';', names=["prefix","next_hop"])
    df['v'] = df["prefix"].map(lambda x : 6 if ':' in x else 4)
    df[['addr','prefixlen']] = df['prefix'].str.split('/',expand=True)
    df['prefixlen'] = df['prefixlen'].astype(int)
    df['metric'] = 0x8000
    
    """ IPv4 """
    
    #df.loc[df['v']==4,'nhn'] = df.loc[df['v']==4,'next_hop'].map(iptohex)
    df.loc[df['v']==4,'nhn'] = df.loc[df['v']==4,'next_hop'].map(lambda x: int(''.join([f'{int(i):0x}' for i in x.split('.')]),16))
    df.loc[df['v']==4,'addr'] = df.loc[df['v']==4,'addr'].map(lambda x: ''.join([f'{int(i):02x}' for i in x.split('.')]))
    df.loc[df['v']==4,'mask'] = df.loc[df['v']==4,'prefixlen'].map(lambda x: f'{(msk4 << (32 - x)) & msk4:08x}')
    df.loc[df['v']==4,'nhn'] = df.loc[df['v']==4,'nhn'] - df.loc[df['v']==4,'nhn'].min()
    
    """ IPv6 """
    """ using ipaddress 2 times cost around 3 sec """
    df.loc[df['v']==6,'nhn'] = df.loc[df['v']==6,'next_hop'].map(lambda x : int(ipaddress.ip_network(x).network_address))
    df.loc[df['v']==6,'addr'] = df.loc[df['v']==6,'addr'].map(lambda x : f'{int(ipaddress.ip_network(x).network_address):032x}')
    df.loc[df['v']==6,'mask'] = df.loc[df['v']==6,'prefixlen'].map(lambda x: f'{(msk6 << (128 - x)) & msk6:032x}')
    df.loc[df['v']==6,'nhn'] = df.loc[df['v']==6,'nhn'] - df.loc[df['v']==6,'nhn'].min()
    
    return df
    
def meth2(filename):
    #25.546343207359314
    df = pd.read_csv(filename, sep=';', names=["prefix","next_hop"])
    df['mask'] = df["prefix"].map(lambda x : f'{int(ipaddress.ip_network(x).netmask):032x}')
    df['addr'] = df["prefix"].map(lambda x : f'{int(ipaddress.ip_network(x).network_address):032x}')
    df['nhn'] = df["next_hop"].map(lambda x : f'{int(ipaddress.ip_network(x).network_address):032x}')
    df['v'] = df["prefix"].map(lambda x : int(ipaddress.ip_network(x).version))
    df['prefixlen'] = df["prefix"].str.split('/').str[1].astype(int)
    df['metric'] = 32768

def meth3(filename):
    #17.901314973831177
    msk4 = int('f' * 8,16)
    msk6 = int('f' * 32,16)

    #print(msk4)
    #print(msk6)

    df = pd.read_csv(filename, sep=';', names=["prefix","next_hop"])
    df['v'] = df["prefix"].map(lambda x : 6 if ':' in x else 4)
    df[['addr','prefixlen']] = df['prefix'].str.split('/',expand=True)
    df['prefixlen'] = df['prefixlen'].astype(int)
    df['metric'] = 32768

    temp = df.loc[df['v']==4,['addr','next_hop']].apply(lambda x: [''.join([f'{int(j):02x}' for j in i]) for i in x.str.split('.')])
    df.loc[df['v']==4,'addr'] = temp['addr']
    df.loc[df['v']==4,'nhn'] = temp['next_hop']
    df.loc[df['v']==4,'mask'] = df.loc[df['v']==4,'prefixlen'].map(lambda x: f'{(msk4 << (32 - x)) & msk4:08x}')

    #IPv6
    temp = df.loc[df['v']==6,['addr','next_hop']].apply(lambda x : [ipaddress.ip_network(i).network_address.exploded.replace(':','') for i in x])
    df.loc[df['v']==6,'addr'] = temp['addr']
    df.loc[df['v']==6,'nhn'] = temp['next_hop']
    df.loc[df['v']==6,'mask'] = df.loc[df['v']==6,'prefixlen'].map(lambda x: f'{(msk6 << (128 - x)) & msk6:032x}')
    
#print(dfv6) 0b1000000000000000



def lpm(df, ipaddr):
    ipad = ipaddr.network_address
    result = []
    for row in df.itertuples():
        if(int(row.mask,16) & int(ipad) == int(row.addr,16) and int(row.v) == ipad.version):
            result.append(row[0])
    return df.loc[result]
    
"""
end = 0
for _ in range(10):
    start = time()
    meth1('routes.txt')
    end += time() - start
print(end/10)

end = 0
for _ in range(10):
    start = time()
    meth2('routes.txt')
    end += time() - start
print(end/10)
"""
"""
async def lpm(prefix,df):
    ipadd = ipaddress.ip_network(prefix)
    result = []
    for row in df.itertuples():
        temp = ipaddress.ip_network(row[1])
        if temp.version == ipadd.version and ipadd.subnet_of(temp):
            result.append(row)
    return pd.DataFrame(result)
"""
"""
@app.on_event("startup")
async def startup():
    pass

@app.on_event("shutdown")
async def shutdown():
    pass
"""

#df['addr'].map(lambda x: int(x,16) & 0xf3)

def lpm2(df,prefix):
    ipadd = prefix.network_address
    int_ipadd = int(ipadd)
    if ipadd.version == 4:
        mas_ip = df.loc[df['v']==4,'mask'].map(lambda x : f'{int(x,16) & int_ipadd:08x}')
        mask = df.loc[df['v']==4,'addr'] == mas_ip
    else:
        mas_ip = df.loc[df['v']==6,'mask'].map(lambda x : f'{int(x,16) & int_ipadd:032x}')
        mask = df.loc[df['v']==6,'addr'] == mas_ip
    return df.loc[mask.loc[mask].index]

df = meth1('routes.txt')
ipadd = ipaddress.ip_network('151.251.225.48')

end = 0
for _ in range(10):
    start = time()
    lpm2(df,ipadd)
    end += time() - start
print(end/10)

end = 0
for _ in range(10):
    start = time()
    lpm(df,ipadd)
    end += time() - start
print(end/10)


