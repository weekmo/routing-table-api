"""Main FastAPI application for routing table service."""

from typing import Dict
import ipaddress

from fastapi import FastAPI, HTTPException
from starlette.responses import RedirectResponse
import uvicorn

from service.config import settings
from service.utils.data import get_df_polars, lpm_update, lpm_map

# Read and prepare routing table data
df = get_df_polars(settings.routes_file, settings.proc_num)

# Create the API object
app = FastAPI(
    title="Routing Table API",
    description="High-performance routing table lookup service with LPM",
    version="0.2.0",
)

@app.get("/")
async def root():
    """Redirect to interactive API documentation."""
    return RedirectResponse(url="/docs")

@app.get("/destination/{prefix:path}")
async def get_nh(prefix: str) -> Dict[str, str]:
    """
    Find the best matching route for a given IP prefix using LPM.
    
    Args:
        prefix: IP prefix in CIDR notation (e.g., "192.168.1.0/24" or "2001:db8::/32")
    
    Returns:
        Dictionary with destination prefix and next hop
    
    Raises:
        HTTPException: 400 if prefix is invalid, 404 if no route found
    """
    # Validate IP prefix
    try:
        ipadd = ipaddress.ip_network(prefix)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid IP prefix: {str(e)}")
    
    # Perform LPM lookup
    next_hop_df = lpm_map(df, ipadd)

    # Check if route exists
    if next_hop_df.empty:
        raise HTTPException(status_code=404, detail="No matching route found")
    
    # Sort by prefix length (longest first), then metric (lowest first), then next hop
    next_hop_df = next_hop_df.sort_values(
        ["prefixlen", "metric", "nhn"], ascending=[False, True, True]
    )
    
    # Return the best match
    best_route = next_hop_df.iloc[0]
    return {"destination": best_route.prefix, "next_hop": best_route.next_hop}

@app.put("/prefix/{prefix:path}/nh/{nh}/metric/{metric}")
async def update_route(prefix: str, nh: str, metric: int) -> Dict[str, str]:
    """
    Update metric for routes matching prefix and next hop.
    
    Args:
        prefix: IP prefix in CIDR notation
        nh: Next hop IP address
        metric: New metric value (0-65535)
    
    Returns:
        Success message
    
    Raises:
        HTTPException: 400 if parameters invalid, 404 if no route found
    """
    # Validate inputs
    try:
        prefix_ip = ipaddress.ip_network(prefix)
        ipaddress.ip_address(nh)  # Validate next hop is an IP
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    "/prefix/{prefix:path}/nh/{nh}/metric/{metric}/match/{match_type}")
async def update_route_with_match(
    prefix: str, nh: str, metric: int, match_type: str
) -> Dict[str, str]:
    """
    Update route metric with specific match criteria.
    
    Args:
        prefix: IP prefix in CIDR notation
        nh: Next hop IP address
        metric: New metric value (0-65535)
        match_type: Either "exact" or "orlonger"
    
    Returns:
        Success message with number of updated routes
    
    Raises:
        HTTPException: 400 if parameters invalid, 404 if no route found
    """
    # Validate match type
    if match_type not in ("exact", "orlonger"):
        raise HTTPException(
            status_code=400, detail="match_type must be 'exact' or 'orlonger'"
        )
    
    # Validate IP parameters
    try:
        prefix_ip = ipaddress.ip_network(prefix)
        ipaddress.ip_address(nh)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    
    if not 0 <= metric <= 65535:
        raise HTTPException(status_code=400, detail="Metric must be between 0 and 65535")
    
    # Update matching routes
    updated_df = lpm_update(df, prefix_ip, nh, metric, matchd=match_type)
host=settings.host, port=settings.port
    if updated_df.empty:
        raise HTTPException(status_code=404, detail="No matching routes found")

    df.update(updated_df)
    return {"status": "success", "updated_routes": len(updated_df)= ipaddress.ip_network(prefix)
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