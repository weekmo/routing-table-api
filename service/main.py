from fastapi import FastAPI, HTTPException
import uvicorn
import ipaddress
import threading
import logging
import sys
from functools import lru_cache
from starlette.responses import RedirectResponse, Response
from typing import Dict, Any
import time
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Local libraries
from service.utils.data import get_df_polars, prep_df, lpm_map, build_radix_tree, lpm_lookup_radix
from service.config import settings
from service.models import RouteResponse, MetricUpdateResponse, HealthResponse
import pandas as pd
from service.utils.radix_tree import RadixTree

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Read and adjust data
logger.info(f"Loading routing table from {settings.routes_file}")
df: pd.DataFrame = get_df_polars(settings.routes_file)
df = prep_df(df)
logger.info(f"Loaded {len(df):,} routes into DataFrame")

# Build radix tree for O(prefix_length) lookups
radix_tree: RadixTree = build_radix_tree(df)

# Thread safety lock for dataframe updates
df_lock = threading.RLock()
logger.info("Service initialization complete")

# Prometheus metrics
lookup_counter = Counter('routing_lookups_total', 'Total number of routing lookups', ['status'])
lookup_latency = Histogram('routing_lookup_latency_seconds', 'Routing lookup latency in seconds')
update_counter = Counter('routing_updates_total', 'Total number of route updates', ['match_type', 'status'])
cache_hits = Counter('routing_cache_hits_total', 'Total number of cache hits')
cache_misses = Counter('routing_cache_misses_total', 'Total number of cache misses')
routes_gauge = Gauge('routing_table_routes', 'Current number of routes in routing table')
error_counter = Counter('routing_errors_total', 'Total number of errors', ['error_type'])

# Set initial routes gauge
routes_gauge.set(len(df))

# LRU cache for frequent lookups (cache up to 10000 recent lookups)
@lru_cache(maxsize=10000)
def cached_radix_lookup(ip_str: str) -> tuple:
    """Cached radix tree lookup. Returns (prefix, next_hop, metric) or None."""
    cache_misses.inc()
    result = radix_tree.lookup(ip_str)
    if result:
        return (result['prefix'], result['next_hop'], result['metric'])
    return None

def get_cached_route(ip_str: str) -> Dict[str, Any]:
    """Get route with cache statistics tracking."""
    # Try cache first
    cached_result = cached_radix_lookup(ip_str)
    if cached_result:
        cache_hits.inc()
        return {
            'prefix': cached_result[0],
            'next_hop': cached_result[1],
            'metric': cached_result[2]
        }
    return None

# Creat the API object
app = FastAPI(
    title="Routing Table API",
    description="High-performance routing table lookup service with LPM (Longest Prefix Match) algorithm. Uses radix tree for O(prefix_length) lookups with caching and monitoring.",
    version="0.2.0",
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "GPL-3.0-or-later",
        "url": "https://www.gnu.org/licenses/gpl-3.0.html",
    },
)


def lpm_update(df, prefix_ip,nh,metric,matchd="orlonger"):
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
        next_hop_df = lpm_map(df, prefix_ip)
        next_hop_df = next_hop_df.loc[(next_hop_df['next_hop'] == nh) & (next_hop_df['prefixlen'] !=0)]
    
    # Update dataframe
    next_hop_df['metric'] = metric
    df.update(next_hop_df)
    
    # Update radix tree to keep in sync
    radix_tree.update_metric(
        prefix=prefix_ip.with_prefixlen,
        next_hop=nh,
        metric=metric,
        match_type=matchd
    )
    
    return next_hop_df

@app.get("/", include_in_schema=False)
async def root():
    """
    Redirect to interactive API documentation.
    """
    return RedirectResponse(url='/docs')

@app.get("/metrics", include_in_schema=False)
async def metrics():
    """
    Prometheus metrics endpoint.
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Health check endpoint for monitoring and load balancers. Returns service status and route counts.",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "routes_loaded": 1090210,
                        "radix_tree_routes": 1090210
                    }
                }
            }
        }
    }
)
async def health() -> HealthResponse:
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns service status and route counts.
    """
    routes_loaded = len(df)
    radix_routes = radix_tree.route_count
    
    # Service is healthy if both DataFrame and radix tree are consistent
    status = "healthy" if routes_loaded == radix_routes else "degraded"
    
    logger.debug(f"Health check: {status}, routes={routes_loaded}")
    
    return HealthResponse(
        status=status,
        routes_loaded=routes_loaded,
        radix_tree_routes=radix_routes
    )

@app.get(
    '/destination/{prefix}',
    response_model=RouteResponse,
    summary="Lookup Route",
    description="""Perform routing table lookup for a destination IP address using LPM (Longest Prefix Match).
    
    The lookup uses a radix tree for O(prefix_length) complexity with LRU caching for frequent destinations.
    
    **Selection criteria (in order):**
    1. Longest prefix match
    2. Lowest metric value
    3. Lowest next-hop IP (tie-breaker)
    """,
    responses={
        200: {
            "description": "Route found successfully",
            "content": {
                "application/json": {
                    "example": {
                        "dst": "192.168.1.0/24",
                        "nh": "10.0.0.1"
                    }
                }
            }
        },
        400: {"description": "Invalid IP address format"},
        404: {"description": "No matching route found"}
    }
)
async def get_nh(prefix: str) -> RouteResponse:
    """
    Perform routing table lookup for a destination IP address.
    
    Returns the best matching route based on:
    1. Longest prefix match
    2. Lowest metric (if multiple matches with same prefix length)
    3. Lowest next-hop IP address (tie-breaker)
    
    Args:
        prefix: IP address to lookup (e.g., "192.168.1.100")
    
    Returns:
        RouteResponse with destination prefix and next hop
    
    Raises:
        HTTPException: 400 if invalid IP, 404 if no route found
    """
    start_time = time.time()
    
    # Verify prefix is an IP address
    try:
        ipadd = ipaddress.ip_network(prefix)
    except (ValueError, ipaddress.AddressValueError) as e:
        logger.warning(f"Invalid IP address lookup attempt: {prefix}")
        error_counter.labels(error_type='invalid_ip').inc()
        lookup_counter.labels(status='error').inc()
        raise HTTPException(status_code=400, detail=f"The given prefix is not correct: {e}")
    
    # Try cached lookup first
    ip_str = str(ipadd.network_address)
    cached_result = get_cached_route(ip_str)
    
    if cached_result:
        lookup_latency.observe(time.time() - start_time)
        lookup_counter.labels(status='success').inc()
        logger.debug(f"Lookup (cached) {prefix} -> {cached_result['prefix']} via {cached_result['next_hop']}")
        return RouteResponse(dst=cached_result['prefix'], nh=cached_result['next_hop'])
    
    # Cache miss - do full lookup with DataFrame
    with df_lock:
        next_hop_df = lpm_lookup_radix(radix_tree, ip_str)

        # Verify dataframe is not empty
        if next_hop_df.empty:
            logger.info(f"No route found for {prefix}")
            error_counter.labels(error_type='no_route').inc()
            lookup_counter.labels(status='not_found').inc()
            lookup_latency.observe(time.time() - start_time)
            raise HTTPException(status_code=404, detail="No route is found")
        
        # Sort to depends on network prefix lenght, metric and next hop
        next_hop_df.sort_values(['prefixlen','metric','nhn'], ascending=[False,True,True],inplace=True)
        
        # Get the first route after sorting
        nh = next_hop_df.iloc[0]
    
    lookup_latency.observe(time.time() - start_time)
    lookup_counter.labels(status='success').inc()
    logger.debug(f"Lookup {prefix} -> {nh.prefix} via {nh.next_hop}")
    return RouteResponse(dst=nh.prefix, nh=nh.next_hop)

@app.put(
    '/prefix/{prefix:path}/nh/{nh}/metric/{metric}',
    response_model=MetricUpdateResponse,
    summary="Update Route Metric (orlonger)",
    description="""Update metric for all routes matching the specified prefix and next hop.
    
    Uses 'orlonger' match by default - updates the exact prefix and all more-specific subnets.
    
    **Example:** Updating 10.0.0.0/8 will also update 10.1.0.0/16, 10.1.1.0/24, etc.
    """,
    responses={
        200: {
            "description": "Routes updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "updated_routes": 5
                    }
                }
            }
        },
        400: {"description": "Invalid parameters (metric out of range or invalid IP)"},
        404: {"description": "No matching routes found"}
    }
)
async def update(prefix: str, nh: str, metric: int) -> MetricUpdateResponse:
    """
    Update metric for all routes matching prefix and next hop (orlonger).
    
    Args:
        prefix: Network prefix in CIDR notation (URL-encoded, e.g., "10.0.0.0%2F8")
        nh: Next hop IP address
        metric: New metric value (1-32768, lower is preferred)
    
    Returns:
        MetricUpdateResponse with number of routes updated
    
    Raises:
        HTTPException: 400 if invalid parameters, 404 if no routes found
    """
    # Validate metric range
    if metric < 1 or metric > settings.max_metric:
        logger.warning(f"Invalid metric value: {metric}")
        error_counter.labels(error_type='invalid_metric').inc()
        update_counter.labels(match_type='orlonger', status='error').inc()
        raise HTTPException(status_code=400, detail=f"Metric must be between 1 and {settings.max_metric}")
    
    # Verify prefix and next hop are IPs
    try:
        prefix_ip = ipaddress.ip_network(prefix)
        ipaddress.ip_network(nh)
    except (ValueError, ipaddress.AddressValueError) as e:
        logger.warning(f"Invalid IP in update: prefix={prefix}, nh={nh}")
        error_counter.labels(error_type='invalid_ip').inc()
        update_counter.labels(match_type='orlonger', status='error').inc()
        raise HTTPException(status_code=400, detail=f"Invalid IP address or prefix: {e}")
    
    # Get search result in sub-dataframe (with write lock)
    with df_lock:
        next_hop_df = lpm_update(df, prefix_ip, nh, metric)
        
        # Verify dataframe is not empty
        if next_hop_df.empty:
            logger.info(f"No routes found to update: {prefix} via {nh}")
            update_counter.labels(match_type='orlonger', status='not_found').inc()
            raise HTTPException(status_code=404, detail="No route is found")
        
        updated_count = len(next_hop_df)
        # Clear cache since routes changed
        cached_radix_lookup.cache_clear()
    
    update_counter.labels(match_type='orlonger', status='success').inc()
    logger.info(f"Updated {updated_count} routes: {prefix} via {nh} metric={metric}")
    return MetricUpdateResponse(status="success", updated_routes=updated_count)

@app.put(
    '/prefix/{prefix:path}/nh/{nh}/metric/{metric}/match/{matchd}',
    response_model=MetricUpdateResponse,
    summary="Update Route Metric (with match type)",
    description="""Update metric for routes with specified match type.
    
    **Match types:**
    - `exact`: Only update routes with exactly this prefix
    - `orlonger`: Update this prefix and all more-specific subnets
    
    **Examples:**
    - `exact` on 10.0.0.0/8: Only updates 10.0.0.0/8
    - `orlonger` on 10.0.0.0/8: Updates 10.0.0.0/8, 10.1.0.0/16, 10.1.1.0/24, etc.
    """,
    responses={
        200: {
            "description": "Routes updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "updated_routes": 1
                    }
                }
            }
        },
        400: {"description": "Invalid parameters (metric out of range, invalid IP, or invalid match type)"},
        404: {"description": "No matching routes found"}
    }
)
async def update_match(prefix: str, nh: str, metric: int, matchd: str) -> MetricUpdateResponse:
    """
    Update metric for routes with specified match type.
    
    Args:
        prefix: Network prefix in CIDR notation (URL-encoded, e.g., "192.168.1.0%2F24")
        nh: Next hop IP address  
        metric: New metric value (1-32768, lower is preferred)
        matchd: Match type - "exact" for exact prefix, "orlonger" for prefix and subnets
    
    Returns:
        MetricUpdateResponse with number of routes updated
    
    Raises:
        HTTPException: 400 if invalid parameters, 404 if no routes found
    """
    # Validate metric range
    if metric < 1 or metric > settings.max_metric:
        logger.warning(f"Invalid metric value: {metric}")
        error_counter.labels(error_type='invalid_metric').inc()
        update_counter.labels(match_type=matchd, status='error').inc()
        raise HTTPException(status_code=400, detail=f"Metric must be between 1 and {settings.max_metric}")
    
    # Verify matchd is valid
    if matchd not in ["orlonger", "exact"]:
        logger.warning(f"Invalid match type: {matchd}")
        error_counter.labels(error_type='invalid_match_type').inc()
        update_counter.labels(match_type=matchd, status='error').inc()
        raise HTTPException(status_code=400, detail="Match classifier must be 'exact' or 'orlonger'")
    
    # Verify prefix and next hop are IPs
    try:
        prefix_ip = ipaddress.ip_network(prefix)
        ipaddress.ip_network(nh)
    except (ValueError, ipaddress.AddressValueError) as e:
        logger.warning(f"Invalid IP in update: prefix={prefix}, nh={nh}")
        error_counter.labels(error_type='invalid_ip').inc()
        update_counter.labels(match_type=matchd, status='error').inc()
        raise HTTPException(status_code=400, detail=f"Invalid IP address or prefix: {e}")
    
    # Get search result in sub-dataframe (FIX: use matchd parameter instead of hardcoded "orlonger") with write lock
    with df_lock:
        next_hop_df = lpm_update(df, prefix_ip, nh, metric, matchd=matchd)
        
        if next_hop_df.empty:
            logger.info(f"No routes found to update: {prefix} via {nh} ({matchd})")
            update_counter.labels(match_type=matchd, status='not_found').inc()
            raise HTTPException(status_code=404, detail="No route is found")
        
        updated_count = len(next_hop_df)
        # Clear cache since routes changed
        cached_radix_lookup.cache_clear()

    update_counter.labels(match_type=matchd, status='success').inc()
    logger.info(f"Updated {updated_count} routes ({matchd}): {prefix} via {nh} metric={metric}")
    return MetricUpdateResponse(status="success", updated_routes=updated_count)

if __name__ == "__main__":
    uvicorn.run(app, port=settings.port, host=settings.host)