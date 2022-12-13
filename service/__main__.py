from fastapi import FastAPI, HTTPException
import uvicorn
import ipaddress
from starlette.responses import RedirectResponse

from service.utils.data import get_df_polars, prep_df, lpm_map

HOST='0.0.0.0'
PORT = 5000

#df = get_df_polars("service/routes.txt")
df = get_df_polars("routes.txt")
df = prep_df(df)

app = FastAPI(title="Get Routing Table")

"""
All subnet with the same next hop
"""
async def lpm_update(df, prefix_ip,nh,metric,matchd="orlonger"):
    
    if matchd == "exact":
        next_hop_df = df.loc[(df['next_hop'] == nh) & (df['prefix'] == prefix_ip.with_prefixlen)]
    else:
        next_hop_df = await lpm_map(df, prefix_ip)
        next_hop_df = next_hop_df.loc[(next_hop_df['next_hop'] == nh) & (next_hop_df['prefixlen'] !=0)]

    next_hop_df['metric'] = metric
    df.update(next_hop_df)
    return next_hop_df

@app.get("/")
async def root():
    return RedirectResponse(url='/docs')

@app.get('/destination/{prefix}')
async def get_nh(prefix: str):
    try:
        ipadd = ipaddress.ip_network(prefix)
    except:
        raise HTTPException(status_code=400, detail="The given prefix is not correct")
    next_hop_df = await lpm_map(df,ipadd)
    if next_hop_df.empty:
        raise HTTPException(status_code=404, detail="No route is found")
    next_hop_df.sort_values(['prefixlen','metric','nhn'], ascending=[False,True,True],inplace=True)
    nh = next_hop_df.iloc[0]
    return {"dst":nh.prefix,"nh":nh.next_hop}

# TODO: add functionality to below functions
@app.put('/prefix/{prefix:path}/nh/{nh}/metric/{metric}')
async def update(prefix,nh,metric: int):
    try:
        prefix_ip = ipaddress.ip_network(prefix)
        ipaddress.ip_network(nh)
    except:
        raise HTTPException(status_code=400, detail="Please review the params")
    next_hop_df = await lpm_update(df, prefix_ip,nh,metric)
    if next_hop_df.empty:
        raise HTTPException(status_code=404, detail="No route is found")
    return {'Done'}

@app.put('/prefix/{prefix:path}/nh/{nh}/metric/{metric}/match/{matchd}')
async def update_match(prefix,nh,metric:int,matchd):
    try:
        assert (matchd == "orlonger" or matchd == "exact")
        prefix_ip = ipaddress.ip_network(prefix)
        ipaddress.ip_network(nh)
    except:
        raise HTTPException(status_code=400, detail="Please review the params")
    next_hop_df = await lpm_update(df, prefix_ip,nh,metric,matchd="orlonger")
    if next_hop_df.empty:
        raise HTTPException(status_code=404, detail="No route is found")
    return {'Done'}

if __name__ == "__main__":
    uvicorn.run(app, port=PORT,host=HOST)