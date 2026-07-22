from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from io import StringIO
import csv

from app.db.session import get_db
from app.schemas.audit_log_schema import AuditLogResponse
from app.controllers.audit_log_controller import (
    get_audit_logs,
    get_audit_log_by_id,
    get_user_audit_logs
)
from app.auth.dependencies import get_current_admin_user

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("", response_model=List[AuditLogResponse])
@router.get("/", response_model=List[AuditLogResponse])
def read_audit_logs(
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    resource: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
):
    """Get audit logs with optional filters (Admin only)"""
    logs = get_audit_logs(
        db,
        user_id=user_id,
        action=action,
        resource=resource,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    return logs


@router.get("/user/{user_id}", response_model=List[AuditLogResponse])
def read_user_audit_logs(
    user_id: int,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
):
    """Get all audit logs for a specific user (Admin only)"""
    return get_user_audit_logs(db, user_id, limit=limit)


@router.get("/export/csv")
def export_audit_logs_csv(
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    resource: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
):
    """Export audit logs to CSV (Admin only)"""
    logs = get_audit_logs(
        db,
        user_id=user_id,
        action=action,
        resource=resource,
        start_date=start_date,
        end_date=end_date,
        limit=10000,
        offset=0
    )
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "User ID", "Action", "Resource", "Resource ID",
        "Timestamp", "IP Address", "Status", "Details"
    ])
    
    for log in logs:
        writer.writerow([
            log.id,
            log.user_id,
            log.action,
            log.resource,
            log.resource_id,
            log.timestamp,
            log.ip_address,
            log.status,
            log.details
        ])
    
    return {
        "filename": f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "content": output.getvalue()
    }


@router.get("/{log_id}", response_model=AuditLogResponse)
def read_audit_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
):
    """Get a specific audit log (Admin only)"""
    return get_audit_log_by_id(db, log_id)
