import asyncio
import logging
from typing import Any, List, Optional
from datetime import datetime
from fastmcp import FastMCP
from pydantic import BaseModel, validator

## logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


## MCP server

mcp = FastMCP("CustomerServiceAssistant")

## Data models

class Customer(BaseModel):
    id: str
    name: str
    email : str
    phone: Optional[str] = None
    account_status: str = "active"
    last_activity: Optional[datetime] = None

    @validator("email")
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError("Invalid email address")
        return v

    