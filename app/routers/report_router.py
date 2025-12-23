
from fastapi import APIRouter, Depends, Query
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
    SalesReportResponse, InventoryReportResponse, CustomerReportResponse
)

router = APIRouter(
    prefix="/reports",
    tags=["Reports & Analytics"]
)


# ===========================================
# 📊 1. SALES REPORT
# ===========================================
@router.get("/sales", response_model=SalesReportResponse)
def get_sales_report(
    date_range_type: DateRangeType = Query(
        default=DateRangeType.LAST_30_DAYS,
        description="Date range: today, yesterday, last_7_days, last_30_days, this_month, last_month, this_year, custom"
    ),
    start_date: Optional[date] = Query(default=None, description="Custom start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(default=None, description="Custom end date (YYYY-MM-DD)"),
    limit: int = Query(default=10, ge=1, le=50, description="Limit for top products"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📊 **Sales & Order Report**
    
    Get comprehensive sales analytics including:
    
    **Summary:**
    - Total orders, revenue, tax, shipping, discounts
    - Net revenue and average order value
    - Order status breakdown (pending, processing, shipped, delivered, cancelled)
    - Payment status breakdown (pending, paid, failed, refunded)
    
    **Details:**
    - Daily sales breakdown (date, orders, revenue, items sold)
    - Top selling products (with category, brand, quantity, revenue)
    - Sales by category (with percentage breakdown)
    - Sales by brand (with percentage breakdown)
    """
    return ReportService.get_sales_report(
        db=db,
        date_range_type=date_range_type,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )


# ===========================================
# 📦 2. INVENTORY REPORT
# ===========================================
@router.get("/inventory", response_model=InventoryReportResponse)
def get_inventory_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📦 **Inventory Report**
    
    Get comprehensive inventory status and alerts:
    
    **Summary:**
    - Total products and variants
    - Total stock, reserved, and available quantities
    - Low stock count
    - Out of stock count
    - Items needing reorder
    - Expiring soon count
    - Total inventory value
    
    **Details:**
    - Inventory by category (product count, stock levels, alerts)
    - Low stock items (product, variant, SKU, quantities, thresholds)
    - Out of stock items
    - Recent stock movements
    """
    return ReportService.get_inventory_report(db)


# ===========================================
# 👥 3. CUSTOMER REPORT
# ===========================================
@router.get("/customers", response_model=CustomerReportResponse)
def get_customer_report(
    date_range_type: DateRangeType = Query(default=DateRangeType.LAST_30_DAYS),
    start_date: Optional[date] = Query(default=None, description="Custom start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(default=None, description="Custom end date (YYYY-MM-DD)"),
    limit: int = Query(default=10, ge=1, le=50, description="Limit for top customers"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    👥 **Customer Report**
    
    Get customer analytics and purchase history:
    
    **Summary:**
    - Total customers
    - New customers (in date range)
    - Active customers (with orders)
    - Verified customers
    - Repeat customers
    - Average customer value
    - Customer acquisition rate
    
    **Details:**
    - Customer segments by spending (VIP, Regular, Occasional, New)
    - Top customers (name, email, orders, total spent, AOV, dates)
    - Activity trends
    """
    return ReportService.get_customer_report(
        db=db,
        date_range_type=date_range_type,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )


# ===========================================
# 📥 4. EXPORT REPORTS (CSV)
# ===========================================
@router.get("/export/{report_type}")
def export_report(
    report_type: str,
    date_range_type: DateRangeType = Query(default=DateRangeType.LAST_30_DAYS),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📥 **Export Reports as CSV**
    
    Download reports in CSV format.
    
    **Report Types:**
    - `sales` - Export all orders with order number, date, status, amounts
    - `inventory` - Export all inventory items with stock levels
    - `customers` - Export customer data with purchase history
    
    **Usage:**
    - GET /api/reports/export/sales
    - GET /api/reports/export/inventory
    - GET /api/reports/export/customers
    """
    if report_type == "sales":
        csv_content, filename = ReportService.export_sales_report(
            db=db,
            date_range_type=date_range_type,
            start_date=start_date,
            end_date=end_date
        )
    elif report_type == "inventory":
        csv_content, filename = ReportService.export_inventory_report(db)
    elif report_type == "customers":
        csv_content, filename = ReportService.export_customer_report(
            db=db,
            date_range_type=date_range_type,
            start_date=start_date,
            end_date=end_date
        )
    else:
        return {"error": f"Invalid report type: {report_type}. Use: sales, inventory, customers"}
    
    return StreamingResponse(
        io.BytesIO(csv_content),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
