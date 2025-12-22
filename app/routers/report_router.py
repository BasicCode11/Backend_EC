from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
import io

from app.database import get_db
from app.deps.auth import get_current_user 
from app.models.user import User
from app.services.report_service import ReportService
from app.schemas.report import (
    DateRangeType, ExportFormat,
    SalesReportResponse, InventoryReportResponse, CustomerReportResponse,
    AnalyticsDashboardResponse, QuickStatsResponse, ExportResponse
)

router = APIRouter(
    prefix="/reports",
    tags=["Reports & Analytics"]
)


# ===========================================
# 🔍 QUICK STATS (Dashboard Widgets)
# ===========================================
@router.get("/quick-stats", response_model=QuickStatsResponse)
def get_quick_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get quick stats for dashboard widgets.
    
    Returns:
    - Today's revenue and orders
    - Pending orders count
    - Low stock alerts count
    - New customers today
    - Comparison with yesterday (growth rates)
    """
    return ReportService.get_quick_stats(db)


# ===========================================
# 📊 SALES/ORDER REPORTS
# ===========================================
@router.get("/sales", response_model=SalesReportResponse)
def get_sales_report(
    date_range_type: DateRangeType = Query(
        default=DateRangeType.LAST_30_DAYS,
        description="Predefined date range type"
    ),
    start_date: Optional[date] = Query(
        default=None,
        description="Custom start date (required if date_range_type is 'custom')"
    ),
    end_date: Optional[date] = Query(
        default=None,
        description="Custom end date (required if date_range_type is 'custom')"
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Limit for top products list"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive sales report.
    
    Returns:
    - Sales summary (total orders, revenue, tax, shipping, discounts)
    - Daily sales breakdown
    - Top selling products
    - Sales by category
    - Sales by brand
    """
    return ReportService.get_sales_report(
        db=db,
        date_range_type=date_range_type,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )


@router.get("/sales/summary")
def get_sales_summary(
    date_range_type: DateRangeType = Query(default=DateRangeType.LAST_30_DAYS),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get only the sales summary (quick endpoint)."""
    start_dt, end_dt = ReportService.get_date_range(date_range_type, start_date, end_date)
    return ReportService.get_sales_summary(db, start_dt, end_dt)


@router.get("/sales/top-products")
def get_top_selling_products(
    date_range_type: DateRangeType = Query(default=DateRangeType.LAST_30_DAYS),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get top selling products."""
    start_dt, end_dt = ReportService.get_date_range(date_range_type, start_date, end_date)
    return ReportService.get_top_selling_products(db, start_dt, end_dt, limit)


@router.get("/sales/by-category")
def get_sales_by_category(
    date_range_type: DateRangeType = Query(default=DateRangeType.LAST_30_DAYS),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get sales breakdown by category."""
    start_dt, end_dt = ReportService.get_date_range(date_range_type, start_date, end_date)
    return ReportService.get_sales_by_category(db, start_dt, end_dt)


@router.get("/sales/by-brand")
def get_sales_by_brand(
    date_range_type: DateRangeType = Query(default=DateRangeType.LAST_30_DAYS),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get sales breakdown by brand."""
    start_dt, end_dt = ReportService.get_date_range(date_range_type, start_date, end_date)
    return ReportService.get_sales_by_brand(db, start_dt, end_dt)


@router.get("/sales/daily")
def get_daily_sales(
    date_range_type: DateRangeType = Query(default=DateRangeType.LAST_30_DAYS),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get daily sales breakdown."""
    start_dt, end_dt = ReportService.get_date_range(date_range_type, start_date, end_date)
    return ReportService.get_daily_sales_breakdown(db, start_dt, end_dt)


# ===========================================
# 📦 INVENTORY REPORTS
# ===========================================
@router.get("/inventory", response_model=InventoryReportResponse)
def get_inventory_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive inventory report.
    
    Returns:
    - Inventory status summary
    - Inventory by category
    - Low stock items
    - Out of stock items
    - Expiring soon items
    """
    return ReportService.get_inventory_report(db)


@router.get("/inventory/status")
def get_inventory_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get inventory status summary."""
    return ReportService.get_inventory_status(db)


@router.get("/inventory/by-category")
def get_inventory_by_category(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get inventory breakdown by category."""
    return ReportService.get_inventory_by_category(db)


@router.get("/inventory/items")
def get_inventory_items(
    status: Optional[str] = Query(
        default=None,
        description="Filter by status: in_stock, low_stock, out_of_stock, needs_reorder"
    ),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get inventory items with optional status filter."""
    return ReportService.get_inventory_items(db, status_filter=status, limit=limit)


# ===========================================
# 👥 CUSTOMER REPORTS
# ===========================================
@router.get("/customers", response_model=CustomerReportResponse)
def get_customer_report(
    date_range_type: DateRangeType = Query(default=DateRangeType.LAST_30_DAYS),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive customer report.
    
    Returns:
    - Customer summary
    - Customer segments by spending
    - Top customers
    - Activity trends
    """
    return ReportService.get_customer_report(
        db=db,
        date_range_type=date_range_type,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )


@router.get("/customers/summary")
def get_customer_summary(
    date_range_type: DateRangeType = Query(default=DateRangeType.LAST_30_DAYS),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get customer summary."""
    start_dt, end_dt = ReportService.get_date_range(date_range_type, start_date, end_date)
    return ReportService.get_customer_summary(db, start_dt, end_dt)


@router.get("/customers/segments")
def get_customer_segments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get customer segments by spending behavior."""
    return ReportService.get_customer_segments(db)


@router.get("/customers/top")
def get_top_customers(
    date_range_type: DateRangeType = Query(default=DateRangeType.LAST_30_DAYS),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get top customers by spending."""
    start_dt, end_dt = ReportService.get_date_range(date_range_type, start_date, end_date)
    return ReportService.get_top_customers(db, start_dt, end_dt, limit)


# ===========================================
# 📈 ANALYTICS DASHBOARD
# ===========================================
@router.get("/analytics", response_model=AnalyticsDashboardResponse)
def get_analytics_dashboard(
    date_range_type: DateRangeType = Query(default=DateRangeType.LAST_30_DAYS),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive analytics dashboard.
    
    Returns:
    - KPI metrics with growth rates
    - Revenue breakdown
    - Order fulfillment metrics
    - Payment metrics
    - Sales trends
    - Top products
    - Sales by category
    """
    return ReportService.get_analytics_dashboard(
        db=db,
        date_range_type=date_range_type,
        start_date=start_date,
        end_date=end_date
    )


# ===========================================
# 📥 EXPORT REPORTS
# ===========================================
@router.get("/export/sales")
def export_sales_report(
    date_range_type: DateRangeType = Query(default=DateRangeType.LAST_30_DAYS),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    format: ExportFormat = Query(default=ExportFormat.CSV),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export sales report as CSV file.
    
    Downloads a CSV file containing all orders in the date range.
    """
    csv_content, filename = ReportService.export_sales_report(
        db=db,
        date_range_type=date_range_type,
        start_date=start_date,
        end_date=end_date,
        format=format
    )
    
    return StreamingResponse(
        io.BytesIO(csv_content),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/export/inventory")
def export_inventory_report(
    format: ExportFormat = Query(default=ExportFormat.CSV),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export inventory report as CSV file.
    
    Downloads a CSV file containing all inventory items.
    """
    csv_content, filename = ReportService.export_inventory_report(db, format)
    
    return StreamingResponse(
        io.BytesIO(csv_content),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/export/customers")
def export_customer_report(
    date_range_type: DateRangeType = Query(default=DateRangeType.LAST_30_DAYS),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    format: ExportFormat = Query(default=ExportFormat.CSV),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export customer report as CSV file.
    
    Downloads a CSV file containing customer data.
    """
    csv_content, filename = ReportService.export_customer_report(
        db=db,
        date_range_type=date_range_type,
        start_date=start_date,
        end_date=end_date,
        format=format
    )
    
    return StreamingResponse(
        io.BytesIO(csv_content),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
