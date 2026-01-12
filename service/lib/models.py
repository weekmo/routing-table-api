"""Pydantic models for routing API requests and responses."""

from pydantic import BaseModel, Field, field_validator
import ipaddress
from typing import Literal


class RouteResponse(BaseModel):
    """Response model for destination lookup."""
    
    dst: str = Field(
        ...,
        description="Destination prefix in CIDR notation",
        examples=["192.168.1.0/24", "2001:db8::/32"]
    )
    nh: str = Field(
        ...,
        description="Next hop IP address",
        examples=["10.0.0.1", "fe80::1"]
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "dst": "192.168.1.0/24",
                    "nh": "10.0.0.1"
                }
            ]
        }
    }


class MetricUpdateResponse(BaseModel):
    """Response model for metric update operations."""
    
    status: Literal["success"] = Field(
        default="success",
        description="Operation status"
    )
    updated_routes: int = Field(
        ...,
        ge=0,
        description="Number of routes updated"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "success",
                    "updated_routes": 5
                }
            ]
        }
    }


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    
    status: Literal["healthy", "degraded"] = Field(
        ...,
        description="Service health status"
    )
    routes_loaded: int = Field(
        ...,
        ge=0,
        description="Number of routes loaded in memory"
    )
    radix_tree_routes: int = Field(
        ...,
        ge=0,
        description="Number of routes in radix tree"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "healthy",
                    "routes_loaded": 1090210,
                    "radix_tree_routes": 1090210
                }
            ]
        }
    }


class MetricUpdateRequest(BaseModel):
    """Internal validation for metric update parameters."""
    
    prefix: str = Field(..., description="Network prefix in CIDR notation")
    next_hop: str = Field(..., description="Next hop IP address")
    metric: int = Field(..., ge=1, le=32768, description="Route metric (1-32768)")
    match_type: Literal["exact", "orlonger"] = Field(
        default="orlonger",
        description="Match type: exact or orlonger"
    )
    
    @field_validator("prefix")
    @classmethod
    def validate_prefix(cls, v: str) -> str:
        """Validate that prefix is a valid network."""
        try:
            ipaddress.ip_network(v)
            return v
        except (ValueError, ipaddress.AddressValueError) as e:
            raise ValueError(f"Invalid network prefix: {e}")
    
    @field_validator("next_hop")
    @classmethod
    def validate_next_hop(cls, v: str) -> str:
        """Validate that next_hop is a valid IP address."""
        try:
            ipaddress.ip_address(v)
            return v
        except (ValueError, ipaddress.AddressValueError) as e:
            raise ValueError(f"Invalid IP address: {e}")
