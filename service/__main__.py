from fastapi import FastAPI, HTTPException
import uvicorn
import ipaddress
from starlette.responses import RedirectResponse
import os
from time import time

# Local libraries
from service.utils.data import get_df_polars, lpm_update, lpm_map

# Server configuration
HOST='0.0.0.0'
PORT = 5000

PROC_NUM = int(os.getenv('PROC_NUM')) or 5
# Read and adjust data
df = get_df_polars("routes.txt",PROC_NUM)

# Creat the API object
app = FastAPI(title="Get Routing Table")

@app.get("/")
async def root():
    """
    Redirect to GUI easiar for using the API
    """
    return RedirectResponse(url='/docs')

@app.get('/destination/{prefix}')
async def get_nh(prefix: str):
    """
    Searching for routes by prefix
    """
    # Verify prefix is an IP address
    try:
        ipadd = ipaddress.ip_network(prefix)
    except:
        raise HTTPException(status_code=400, detail="The given prefix is not correct")
    
    # Get search result in sub-dataframe
    next_hop_df = await lpm_map(df,ipadd)

    # Verify dataframe is not empty
    if next_hop_df.empty:
        raise HTTPException(status_code=404, detail="No route is found")
    
    # Sort to depends on network prefix lenght, metric and next hop
    next_hop_df.sort_values(['prefixlen','metric','nhn'], ascending=[False,True,True],inplace=True)
    
    # Get the first route after sorting
    nh = next_hop_df.iloc[0]
    return {"dst":nh.prefix,"nh":nh.next_hop}

@app.put('/prefix/{prefix:path}/nh/{nh}/metric/{metric}')
async def update(prefix,nh,metric: int):
    """
    Update all subnet routes depending on prefix and next hop
    """
    # Verify prefix and next hop are IPs
    try:
        prefix_ip = ipaddress.ip_network(prefix)
        ipaddress.ip_network(nh)
    except:
        raise HTTPException(status_code=400, detail="Please review the params")
    
    # Get search result in sub-dataframe
    next_hop_df = await lpm_update(df, prefix_ip,nh,metric)
    
    # Verify dataframe is not empty
    if next_hop_df.empty:
        raise HTTPException(status_code=404, detail="No route is found")

    df.update(next_hop_df)
    return {'Done'}

@app.put('/prefix/{prefix:path}/nh/{nh}/metric/{metric}/match/{matchd}')
async def update_match(prefix,nh,metric:int,matchd):
    """
    Update the route depending on prefix and next hop
    """
    # Verify prefix and next hop are IPs and matchd is the correct word
    try:
        assert (matchd == "orlonger" or matchd == "exact")
        prefix_ip = ipaddress.ip_network(prefix)
        ipaddress.ip_network(nh)
    except:
        raise HTTPException(status_code=400, detail="Please review the params")
    
    # Get search result in sub-dataframe
    next_hop_df = await lpm_update(df, prefix_ip,nh,metric,matchd="orlonger")

    # Verify dataframe is not empty
    if next_hop_df.empty:
        raise HTTPException(status_code=404, detail="No route is found")

    df.update(next_hop_df)    
    return {'Done'}

if __name__ == "__main__":
    uvicorn.run(app, port=PORT,host=HOST)