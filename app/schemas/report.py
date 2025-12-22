"""
Report Schemas - Response models for all report types
📊 Sales/Order Reports
📦 Inventory Reports
👥 Customer Reports
📈 Analytics Dashboard
📥 Export Reports
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


# ===========================================
# 📅 DATE RANGE & EXPORT ENUMS
# ===========================================
class DateRangeType(str, Enum):
    TODAY = "today"
    YESTERDAY = "yesterday"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    THIS_YEAR = "this_year"
    CUSTOM = "custom"


class ExportFormat(str, Enum):
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"


# ===========================================
# 📊 SALES/ORDER REPORT SCHEMAS
# ===========================================
class SalesSummary(BaseModel):
    """Summary of sales metrics"""
    total_orders: int = Field(..., description="Total number of orders")
    total_revenue: float = Field(..., description="Total revenue from orders")
    total_tax: float = Field(..., description="Total tax collected")
    total_shipping: float = Field(..., description="Total shipping fees")
    total_discounts: float = Field(..., description="Total discounts applied")
    net_revenue: float = Field(..., description="Net revenue after discounts")
    average_order_value: float = Field(..., description="Average order value")
    orders_pending: int = Field(default=0)
    orders_processing: int = Field(default=0)
    orders_shipped: int = Field(default=0)
    orders_delivered: int = Field(default=0)
    orders_cancelled: int = Field(default=0)
    payment_pending: int = Field(default=0)
    payment_paid: int = Field(default=0)
    payment_failed: int = Field(default=0)
    payment_refunded: int = Field(default=0)


class DailySalesData(BaseModel):
    """Daily sales breakdown"""
    date: date
    orders_count: int
    revenue: float
    items_sold: int


class TopSellingProduct(BaseModel):
    """Top selling product data"""
    product_id: int
    product_name: str
    category_name: Optional[str] = None
    brand_name: Optional[str] = None
    quantity_sold: int
    revenue: float
    order_count: int


class SalesByCategory(BaseModel):
    """Sales breakdown by category"""
    category_id: int
    category_name: str
    total_orders: int
    total_items: int
    revenue: float
    percentage: float


class SalesByBrand(BaseModel):
    """Sales breakdown by brand"""
    brand_id: Optional[int]
    brand_name: str
    total_orders: int
    total_items: int
    revenue: float
    percentage: float


class SalesReportResponse(BaseModel):
    """Complete sales report response"""
    success: bool = True
    report_type: str = "sales"
    date_range: Dict[str, str]
    summary: SalesSummary
    daily_breakdown: List[DailySalesData] = []
    top_products: List[TopSellingProduct] = []
    sales_by_category: List[SalesByCategory] = []
    sales_by_brand: List[SalesByBrand] = []
    generated_at: datetime = Field(default_factory=datetime.now)


class SalesTrendData(BaseModel):
    """Sales trend over time"""
    period: str  # day, week, month
    label: str
    orders: int
    revenue: float
    growth_rate: Optional[float] = None


# ===========================================
# 📦 INVENTORY REPORT SCHEMAS
# ===========================================
class InventoryStatus(BaseModel):
    """Inventory status summary"""
    total_products: int
    total_variants: int
    total_stock_quantity: int
    total_reserved_quantity: int
    total_available_quantity: int
    low_stock_count: int
    out_of_stock_count: int
    reorder_needed_count: int
    expiring_soon_count: int
    total_inventory_value: float


class InventoryByCategory(BaseModel):
    """Inventory breakdown by category"""
    category_id: int
    category_name: str
    product_count: int
    total_stock: int
    available_stock: int
    low_stock_items: int
    out_of_stock_items: int


class InventoryItem(BaseModel):
    """Individual inventory item details"""
    inventory_id: int
    product_id: int
    product_name: str
    variant_id: int
    variant_name: Optional[str] = None
    sku: Optional[str] = None
    stock_quantity: int
    reserved_quantity: int
    available_quantity: int
    low_stock_threshold: int
    reorder_level: int
    location: Optional[str] = None
    status: str  # in_stock, low_stock, out_of_stock, needs_reorder


class StockMovement(BaseModel):
    """Stock movement record"""
    date: datetime
    product_name: str
    variant_name: Optional[str] = None
    movement_type: str  # in, out, adjustment
    quantity: int
    reason: Optional[str] = None


class InventoryReportResponse(BaseModel):
    """Complete inventory report response"""
    success: bool = True
    report_type: str = "inventory"
    summary: InventoryStatus
    by_category: List[InventoryByCategory] = []
    low_stock_items: List[InventoryItem] = []
    out_of_stock_items: List[InventoryItem] = []
    expiring_soon: List[InventoryItem] = []
    recent_movements: List[StockMovement] = []
    generated_at: datetime = Field(default_factory=datetime.now)


# ===========================================
# 👥 CUSTOMER REPORT SCHEMAS
# ===========================================
class CustomerSummary(BaseModel):
    """Customer base summary"""
    total_customers: int
    new_customers: int  # in date range
    active_customers: int  # with orders in date range
    verified_customers: int
    repeat_customers: int
    average_customer_value: float
    customer_acquisition_rate: float  # percentage


class CustomerSegment(BaseModel):
    """Customer segment data"""
    segment_name: str
    customer_count: int
    percentage: float
    total_spent: float
    average_order_value: float


class TopCustomer(BaseModel):
    """Top customer data"""
    user_id: int
    customer_name: str
    email: str
    total_orders: int
    total_spent: float
    average_order_value: float
    first_order_date: Optional[datetime] = None
    last_order_date: Optional[datetime] = None


class CustomerActivity(BaseModel):
    """Customer activity metrics"""
    date: date
    new_registrations: int
    active_customers: int
    orders_placed: int


class CustomerReportResponse(BaseModel):
    """Complete customer report response"""
    success: bool = True
    report_type: str = "customer"
    date_range: Dict[str, str]
    summary: CustomerSummary
    segments: List[CustomerSegment] = []
    top_customers: List[TopCustomer] = []
    activity_trend: List[CustomerActivity] = []
    generated_at: datetime = Field(default_factory=datetime.now)


# ===========================================
# 📈 ANALYTICS DASHBOARD SCHEMAS
# ===========================================
class KPIMetrics(BaseModel):
    """Key Performance Indicators"""
    total_revenue: float
    revenue_growth: float  # percentage compared to previous period
    total_orders: int
    orders_growth: float
    average_order_value: float
    aov_growth: float
    total_customers: int
    new_customers: int
    conversion_rate: float  # orders / visits if available
    cart_abandonment_rate: Optional[float] = None


class RevenueBreakdown(BaseModel):
    """Revenue breakdown"""
    gross_revenue: float
    discounts: float
    refunds: float
    shipping_collected: float
    tax_collected: float
    net_revenue: float


class OrderFulfillment(BaseModel):
    """Order fulfillment metrics"""
    pending_orders: int
    processing_orders: int
    shipped_orders: int
    delivered_orders: int
    cancelled_orders: int
    fulfillment_rate: float  # delivered / total orders
    average_fulfillment_time: Optional[float] = None  # in hours


class PaymentMetrics(BaseModel):
    """Payment-related metrics"""
    pending_amount: float
    paid_amount: float
    failed_amount: float
    refunded_amount: float
    success_rate: float


class AnalyticsDashboardResponse(BaseModel):
    """Complete analytics dashboard response"""
    success: bool = True
    report_type: str = "analytics_dashboard"
    date_range: Dict[str, str]
    kpi: KPIMetrics
    revenue_breakdown: RevenueBreakdown
    order_fulfillment: OrderFulfillment
    payment_metrics: PaymentMetrics
    sales_trend: List[SalesTrendData] = []
    top_products: List[TopSellingProduct] = []
    sales_by_category: List[SalesByCategory] = []
    generated_at: datetime = Field(default_factory=datetime.now)


# ===========================================
# 📥 EXPORT REPORT SCHEMAS
# ===========================================
class ExportRequest(BaseModel):
    """Request for exporting reports"""
    report_type: str = Field(..., description="Type of report: sales, inventory, customer, analytics")
    format: ExportFormat = Field(default=ExportFormat.EXCEL)
    date_range_type: DateRangeType = Field(default=DateRangeType.LAST_30_DAYS)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    include_charts: bool = Field(default=True)


class ExportResponse(BaseModel):
    """Response for export request"""
    success: bool
    message: str
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    download_url: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.now)


# ===========================================
# 🔍 GENERAL REPORT SCHEMAS
# ===========================================
class ReportFilter(BaseModel):
    """Common filters for reports"""
    date_range_type: DateRangeType = Field(default=DateRangeType.LAST_30_DAYS)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    status: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)


class QuickStatsResponse(BaseModel):
    """Quick stats for dashboard widgets"""
    success: bool = True
    today_revenue: float
    today_orders: int
    pending_orders: int
    low_stock_alerts: int
    new_customers_today: int
    compared_to_yesterday: Dict[str, float]  # percentage changes
    generated_at: datetime = Field(default_factory=datetime.now)
