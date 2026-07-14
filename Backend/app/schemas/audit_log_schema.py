import json
from typing import Any, Dict, Optional, Union
from datetime import datetime

from pydantic import BaseModel, field_validator, ConfigDict

class AuditLogCreate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    user_id: Optional[int]
    action: str
    resource: str
    resource_id: Optional[int] = None
    changes: Optional[Union[Dict[str, Any], str]] = None
    ip_address: Optional[str] = None
    status: str = "success"
    details: Optional[str] = None

    @field_validator("changes", mode="before")
    @classmethod
    def parse_changes(cls, value: Any) -> Any:
        if value is None or isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict):
                    return parsed
            except (TypeError, ValueError):
                pass
        return value

class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    id: int
    user_id: Optional[int]
    action: str
    resource: str
    resource_id: Optional[int]
    changes: Optional[Union[Dict[str, Any], str]]
    timestamp: datetime
    ip_address: Optional[str]
    status: str
    details: Optional[str]

    @field_validator("changes", mode="before")
    @classmethod
    def parse_changes(cls, value: Any) -> Any:
        if value is None or isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict):
                    return parsed
            except (TypeError, ValueError):
                pass
        return value

class AuditLogFilter(BaseModel):
    user_id: Optional[int] = None
    action: Optional[str] = None
    resource: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 100
    offset: int = 0
