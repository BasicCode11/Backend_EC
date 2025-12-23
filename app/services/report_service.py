
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, select, and_, or_, extract, desc, case
from decimal import Decimal
import logging
import io
import csv

from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.order_item import OrderItem
from app.models.user import User
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.inventory import Inventory
from app.models.category import Category
from app.models.brand import Brand
from app.models.review import Review
from app.schemas.report import (
    DateRangeType, ExportFormat,
    SalesSummary, DailySalesData, TopSellingProduct, SalesByCategory, SalesByBrand,
    SalesReportResponse, SalesTrendData,
    InventoryStatus, InventoryByCategory, InventoryItem, InventoryReportResponse,
    CustomerSummary, CustomerSegment, TopCustomer, CustomerActivity, CustomerReportResponse,
    KPIMetrics, RevenueBreakdown, OrderFulfillment, PaymentMetrics, AnalyticsDashboardResponse,
    QuickStatsResponse
)

logger = logging.getLogger(__name__)


class ReportService:
    """
    Comprehensive reporting service for e-commerce analytics.
    """
    @staticmethod
    def get_date_range(
        date_range_type: DateRangeType,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Tuple[datetime, datetime]:
        """
        Calculate date range based on type or custom dates.
        Returns tuple of (start_datetime, end_datetime)
        """
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if date_range_type == DateRangeType.CUSTOM and start_date and end_date:
            return (
                datetime.combine(start_date, datetime.min.time()),
                datetime.combine(end_date, datetime.max.time())
            )
        
        ranges = {
            DateRangeType.TODAY: (today, today.replace(hour=23, minute=59, second=59)),
            DateRangeType.YESTERDAY: (
                today - timedelta(days=1),
                (today - timedelta(days=1)).replace(hour=23, minute=59, second=59)
            ),
            DateRangeType.LAST_7_DAYS: (today - timedelta(days=6), today.replace(hour=23, minute=59, second=59)),
            DateRangeType.LAST_30_DAYS: (today - timedelta(days=29), today.replace(hour=23, minute=59, second=59)),
            DateRangeType.THIS_MONTH: (today.replace(day=1), today.replace(hour=23, minute=59, second=59)),
            DateRangeType.LAST_MONTH: (
                (today.replace(day=1) - timedelta(days=1)).replace(day=1),
                today.replace(day=1) - timedelta(seconds=1)
            ),
            DateRangeType.THIS_YEAR: (today.replace(month=1, day=1), today.replace(hour=23, minute=59, second=59)),
        }
        
        return ranges.get(date_range_type, (today - timedelta(days=29), today.replace(hour=23, minute=59, second=59)))

    @staticmethod
    def get_previous_period(start_date: datetime, end_date: datetime) -> Tuple[datetime, datetime]:
        """Get the previous period of the same duration for comparison."""
        duration = end_date - start_date
        prev_end = start_date - timedelta(seconds=1)
        prev_start = prev_end - duration
        return (prev_start, prev_end)

    @staticmethod
    def calculate_growth_rate(current: float, previous: float) -> float:
        """Calculate percentage growth rate."""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 2)

    
    @staticmethod
    def get_sales_summary(
        db: Session,
        start_date: datetime,
        end_date: datetime
    ) -> SalesSummary:
        """Get sales summary for the given date range."""
        try:
            # Query orders in date range
            orders = db.query(Order).filter(
                and_(
                    Order.created_at >= start_date,
                    Order.created_at <= end_date
                )
            ).all()
            
            if not orders:
                return SalesSummary(
                    total_orders=0,
                    total_revenue=0.0,
                    total_tax=0.0,
                    total_shipping=0.0,
                    total_discounts=0.0,
                    net_revenue=0.0,
                    average_order_value=0.0
                )
            
            # Calculate totals
            total_revenue = sum(float(o.total_amount or 0) for o in orders)
            total_tax = sum(float(o.tax_amount or 0) for o in orders)
            total_shipping = sum(float(o.shipping_amount or 0) for o in orders)
            total_discounts = sum(float(o.discount_amount or 0) for o in orders)
            
            # Count by status
            status_counts = {}
            payment_counts = {}
            for order in orders:
                status_counts[order.status] = status_counts.get(order.status, 0) + 1
                payment_counts[order.payment_status] = payment_counts.get(order.payment_status, 0) + 1
            
            return SalesSummary(
                total_orders=len(orders),
                total_revenue=round(total_revenue, 2),
                total_tax=round(total_tax, 2),
                total_shipping=round(total_shipping, 2),
                total_discounts=round(total_discounts, 2),
                net_revenue=round(total_revenue - total_discounts, 2),
                average_order_value=round(total_revenue / len(orders), 2) if orders else 0.0,
                orders_pending=status_counts.get(OrderStatus.PENDING.value, 0),
                orders_processing=status_counts.get(OrderStatus.PROCESSING.value, 0),
                orders_shipped=status_counts.get(OrderStatus.SHIPPED.value, 0),
                orders_delivered=status_counts.get(OrderStatus.DELIVERED.value, 0),
                orders_cancelled=status_counts.get(OrderStatus.CANCELLED.value, 0),
                payment_pending=payment_counts.get(PaymentStatus.PENDING.value, 0),
                payment_paid=payment_counts.get(PaymentStatus.PAID.value, 0),
                payment_failed=payment_counts.get(PaymentStatus.FAILED.value, 0),
                payment_refunded=payment_counts.get(PaymentStatus.REFUNDED.value, 0)
            )
        except Exception as e:
            logger.error(f"Error getting sales summary: {str(e)}")
            raise

    @staticmethod
    def get_daily_sales_breakdown(
        db: Session,
        start_date: datetime,
        end_date: datetime
    ) -> List[DailySalesData]:
        """Get daily sales breakdown."""
        try:
            # Query daily aggregates
            results = db.query(
                func.date(Order.created_at).label('order_date'),
                func.count(Order.id).label('orders_count'),
                func.sum(Order.total_amount).label('revenue')
            ).filter(
                and_(
                    Order.created_at >= start_date,
                    Order.created_at <= end_date,
                    Order.status != OrderStatus.CANCELLED.value
                )
            ).group_by(
                func.date(Order.created_at)
            ).order_by(
                func.date(Order.created_at)
            ).all()
            
            # Get items sold per day
            items_results = db.query(
                func.date(Order.created_at).label('order_date'),
                func.sum(OrderItem.quantity).label('items_sold')
            ).join(
                OrderItem, Order.id == OrderItem.order_id
            ).filter(
                and_(
                    Order.created_at >= start_date,
                    Order.created_at <= end_date,
                    Order.status != OrderStatus.CANCELLED.value
                )
            ).group_by(
                func.date(Order.created_at)
            ).all()
            
            items_by_date = {r.order_date: int(r.items_sold or 0) for r in items_results}
            
            daily_data = []
            for row in results:
                daily_data.append(DailySalesData(
                    date=row.order_date,
                    orders_count=row.orders_count,
                    revenue=float(row.revenue or 0),
                    items_sold=items_by_date.get(row.order_date, 0)
                ))
            
            return daily_data
        except Exception as e:
            logger.error(f"Error getting daily sales breakdown: {str(e)}")
            raise

    @staticmethod
    def get_top_selling_products(
        db: Session,
        start_date: datetime,
        end_date: datetime,
        limit: int = 10
    ) -> List[TopSellingProduct]:
        """Get top selling products by quantity and revenue."""
        try:
            results = db.query(
                OrderItem.product_id,
                OrderItem.product_name,
                func.sum(OrderItem.quantity).label('quantity_sold'),
                func.sum(OrderItem.total_price).label('revenue'),
                func.count(func.distinct(OrderItem.order_id)).label('order_count')
            ).join(
                Order, OrderItem.order_id == Order.id
            ).filter(
                and_(
                    Order.created_at >= start_date,
                    Order.created_at <= end_date,
                    Order.status != OrderStatus.CANCELLED.value
                )
            ).group_by(
                OrderItem.product_id,
                OrderItem.product_name
            ).order_by(
                desc('quantity_sold')
            ).limit(limit).all()
            
            top_products = []
            for row in results:
                # Get category and brand info
                product = db.query(Product).filter(Product.id == row.product_id).first()
                category_name = product.category.name if product and product.category else None
                brand_name = product.brand.name if product and product.brand else None
                
                top_products.append(TopSellingProduct(
                    product_id=row.product_id,
                    product_name=row.product_name,
                    category_name=category_name,
                    brand_name=brand_name,
                    quantity_sold=int(row.quantity_sold or 0),
                    revenue=float(row.revenue or 0),
                    order_count=int(row.order_count or 0)
                ))
            
            return top_products
        except Exception as e:
            logger.error(f"Error getting top selling products: {str(e)}")
            raise

    @staticmethod
    def get_sales_by_category(
        db: Session,
        start_date: datetime,
        end_date: datetime
    ) -> List[SalesByCategory]:
        """Get sales breakdown by category."""
        try:
            results = db.query(
                Category.id.label('category_id'),
                Category.name.label('category_name'),
                func.count(func.distinct(Order.id)).label('total_orders'),
                func.sum(OrderItem.quantity).label('total_items'),
                func.sum(OrderItem.total_price).label('revenue')
            ).join(
                Product, OrderItem.product_id == Product.id
            ).join(
                Category, Product.category_id == Category.id
            ).join(
                Order, OrderItem.order_id == Order.id
            ).filter(
                and_(
                    Order.created_at >= start_date,
                    Order.created_at <= end_date,
                    Order.status != OrderStatus.CANCELLED.value
                )
            ).group_by(
                Category.id,
                Category.name
            ).all()
            
            total_revenue = sum(float(r.revenue or 0) for r in results)
            
            category_sales = []
            for row in results:
                revenue = float(row.revenue or 0)
                category_sales.append(SalesByCategory(
                    category_id=row.category_id,
                    category_name=row.category_name,
                    total_orders=int(row.total_orders or 0),
                    total_items=int(row.total_items or 0),
                    revenue=revenue,
                    percentage=round((revenue / total_revenue * 100) if total_revenue > 0 else 0, 2)
                ))
            
            return sorted(category_sales, key=lambda x: x.revenue, reverse=True)
        except Exception as e:
            logger.error(f"Error getting sales by category: {str(e)}")
            raise

    @staticmethod
    def get_sales_by_brand(
        db: Session,
        start_date: datetime,
        end_date: datetime
    ) -> List[SalesByBrand]:
        """Get sales breakdown by brand."""
        try:
            results = db.query(
                Brand.id.label('brand_id'),
                Brand.name.label('brand_name'),
                func.count(func.distinct(Order.id)).label('total_orders'),
                func.sum(OrderItem.quantity).label('total_items'),
                func.sum(OrderItem.total_price).label('revenue')
            ).join(
                Product, OrderItem.product_id == Product.id
            ).outerjoin(
                Brand, Product.brand_id == Brand.id
            ).join(
                Order, OrderItem.order_id == Order.id
            ).filter(
                and_(
                    Order.created_at >= start_date,
                    Order.created_at <= end_date,
                    Order.status != OrderStatus.CANCELLED.value
                )
            ).group_by(
                Brand.id,
                Brand.name
            ).all()
            
            total_revenue = sum(float(r.revenue or 0) for r in results)
            
            brand_sales = []
            for row in results:
                revenue = float(row.revenue or 0)
                brand_sales.append(SalesByBrand(
                    brand_id=row.brand_id,
                    brand_name=row.brand_name or "No Brand",
                    total_orders=int(row.total_orders or 0),
                    total_items=int(row.total_items or 0),
                    revenue=revenue,
                    percentage=round((revenue / total_revenue * 100) if total_revenue > 0 else 0, 2)
                ))
            
            return sorted(brand_sales, key=lambda x: x.revenue, reverse=True)
        except Exception as e:
            logger.error(f"Error getting sales by brand: {str(e)}")
            raise

    @staticmethod
    def get_sales_report(
        db: Session,
        date_range_type: DateRangeType = DateRangeType.LAST_30_DAYS,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 10
    ) -> SalesReportResponse:
        """Generate complete sales report."""
        try:
            start_dt, end_dt = ReportService.get_date_range(date_range_type, start_date, end_date)
            
            return SalesReportResponse(
                date_range={
                    "start": start_dt.strftime("%Y-%m-%d"),
                    "end": end_dt.strftime("%Y-%m-%d"),
                    "type": date_range_type.value
                },
                summary=ReportService.get_sales_summary(db, start_dt, end_dt),
                daily_breakdown=ReportService.get_daily_sales_breakdown(db, start_dt, end_dt),
                top_products=ReportService.get_top_selling_products(db, start_dt, end_dt, limit),
                sales_by_category=ReportService.get_sales_by_category(db, start_dt, end_dt),
                sales_by_brand=ReportService.get_sales_by_brand(db, start_dt, end_dt)
            )
        except Exception as e:
            logger.error(f"Error generating sales report: {str(e)}")
            raise

    
    @staticmethod
    def get_inventory_status(db: Session) -> InventoryStatus:
        """Get overall inventory status."""
        try:
            # Get all inventory records with product info
            inventories = db.query(Inventory).all()
            
            total_stock = sum(i.stock_quantity for i in inventories)
            total_reserved = sum(i.reserved_quantity or 0 for i in inventories)
            total_available = total_stock - total_reserved
            
            low_stock = [i for i in inventories if i.is_low_stock]
            out_of_stock = [i for i in inventories if i.available_quantity <= 0]
            needs_reorder = [i for i in inventories if i.needs_reorder]
            
            # Count expiring soon (within 30 days)
            expiry_threshold = datetime.now() + timedelta(days=30)
            expiring_soon = [i for i in inventories if i.expiry_date and i.expiry_date <= expiry_threshold]
            
            # Calculate inventory value (stock_quantity * variant price)
            total_value = 0.0
            for inv in inventories:
                if inv.variant and inv.variant.additional_price:
                    total_value += float(inv.variant.additional_price) * inv.stock_quantity
            
            return InventoryStatus(
                total_products=db.query(func.count(Product.id)).scalar() or 0,
                total_variants=db.query(func.count(ProductVariant.id)).scalar() or 0,
                total_stock_quantity=total_stock,
                total_reserved_quantity=total_reserved,
                total_available_quantity=total_available,
                low_stock_count=len(low_stock),
                out_of_stock_count=len(out_of_stock),
                reorder_needed_count=len(needs_reorder),
                expiring_soon_count=len(expiring_soon),
                total_inventory_value=round(total_value, 2)
            )
        except Exception as e:
            logger.error(f"Error getting inventory status: {str(e)}")
            raise

    @staticmethod
    def get_inventory_by_category(db: Session) -> List[InventoryByCategory]:
        """Get inventory breakdown by category."""
        try:
            categories = db.query(Category).all()
            
            result = []
            for cat in categories:
                products = db.query(Product).filter(Product.category_id == cat.id).all()
                product_ids = [p.id for p in products]
                
                if not product_ids:
                    continue
                
                # Get variants for these products
                variants = db.query(ProductVariant).filter(
                    ProductVariant.product_id.in_(product_ids)
                ).all()
                variant_ids = [v.id for v in variants]
                
                if not variant_ids:
                    continue
                
                # Get inventory for these variants
                inventories = db.query(Inventory).filter(
                    Inventory.variant_id.in_(variant_ids)
                ).all()
                
                total_stock = sum(i.stock_quantity for i in inventories)
                available_stock = sum(i.available_quantity for i in inventories)
                low_stock_items = len([i for i in inventories if i.is_low_stock])
                out_of_stock_items = len([i for i in inventories if i.available_quantity <= 0])
                
                result.append(InventoryByCategory(
                    category_id=cat.id,
                    category_name=cat.name,
                    product_count=len(products),
                    total_stock=total_stock,
                    available_stock=available_stock,
                    low_stock_items=low_stock_items,
                    out_of_stock_items=out_of_stock_items
                ))
            
            return result
        except Exception as e:
            logger.error(f"Error getting inventory by category: {str(e)}")
            raise

    @staticmethod
    def get_inventory_items(
        db: Session,
        status_filter: Optional[str] = None,
        limit: int = 50
    ) -> List[InventoryItem]:
        """Get inventory items with optional status filter."""
        try:
            query = db.query(Inventory)
            inventories = query.all()
            
            items = []
            for inv in inventories:
                # Determine status
                if inv.available_quantity <= 0:
                    status = "out_of_stock"
                elif inv.needs_reorder:
                    status = "needs_reorder"
                elif inv.is_low_stock:
                    status = "low_stock"
                else:
                    status = "in_stock"
                
                # Apply filter
                if status_filter and status != status_filter:
                    continue
                
                variant = inv.variant
                product = variant.product if variant else None
                
                items.append(InventoryItem(
                    inventory_id=inv.id,
                    product_id=product.id if product else 0,
                    product_name=product.name if product else "Unknown",
                    variant_id=inv.variant_id,
                    variant_name=variant.variant_name if variant else None,
                    sku=inv.sku,
                    stock_quantity=inv.stock_quantity,
                    reserved_quantity=inv.reserved_quantity or 0,
                    available_quantity=inv.available_quantity,
                    low_stock_threshold=inv.low_stock_threshold,
                    reorder_level=inv.reorder_level,
                    location=inv.location,
                    status=status
                ))
            
            # Sort by status priority and limit
            priority = {"out_of_stock": 0, "needs_reorder": 1, "low_stock": 2, "in_stock": 3}
            items.sort(key=lambda x: priority.get(x.status, 4))
            
            return items[:limit]
        except Exception as e:
            logger.error(f"Error getting inventory items: {str(e)}")
            raise

    @staticmethod
    def get_inventory_report(db: Session) -> InventoryReportResponse:
        """Generate complete inventory report."""
        try:
            all_items = ReportService.get_inventory_items(db, limit=100)
            
            return InventoryReportResponse(
                summary=ReportService.get_inventory_status(db),
                by_category=ReportService.get_inventory_by_category(db),
                low_stock_items=[i for i in all_items if i.status == "low_stock"][:20],
                out_of_stock_items=[i for i in all_items if i.status == "out_of_stock"][:20],
                expiring_soon=[],  # Implement if needed
                recent_movements=[]  # Implement with audit logs if needed
            )
        except Exception as e:
            logger.error(f"Error generating inventory report: {str(e)}")
            raise

    
    @staticmethod
    def get_customer_summary(
        db: Session,
        start_date: datetime,
        end_date: datetime
    ) -> CustomerSummary:
        """Get customer summary for the given date range."""
        try:
            # Total customers
            total_customers = db.query(func.count(User.id)).scalar() or 0
            
            # New customers in date range
            new_customers = db.query(func.count(User.id)).filter(
                and_(
                    User.created_at >= start_date,
                    User.created_at <= end_date
                )
            ).scalar() or 0
            
            # Verified customers
            verified_customers = db.query(func.count(User.id)).filter(
                User.email_verified == True
            ).scalar() or 0
            
            # Active customers (with orders in date range)
            active_customer_ids = db.query(func.distinct(Order.user_id)).filter(
                and_(
                    Order.created_at >= start_date,
                    Order.created_at <= end_date
                )
            ).all()
            active_customers = len(active_customer_ids)
            
            # Repeat customers (more than 1 order ever)
            repeat_customers = db.query(Order.user_id).group_by(
                Order.user_id
            ).having(
                func.count(Order.id) > 1
            ).count()
            
            # Average customer value
            total_revenue = db.query(func.sum(Order.total_amount)).filter(
                Order.status != OrderStatus.CANCELLED.value
            ).scalar() or 0
            avg_customer_value = float(total_revenue) / total_customers if total_customers > 0 else 0
            
            # Customer acquisition rate
            prev_start, prev_end = ReportService.get_previous_period(start_date, end_date)
            prev_total = db.query(func.count(User.id)).filter(
                User.created_at < start_date
            ).scalar() or 0
            acquisition_rate = round((new_customers / prev_total * 100) if prev_total > 0 else 0, 2)
            
            return CustomerSummary(
                total_customers=total_customers,
                new_customers=new_customers,
                active_customers=active_customers,
                verified_customers=verified_customers,
                repeat_customers=repeat_customers,
                average_customer_value=round(avg_customer_value, 2),
                customer_acquisition_rate=acquisition_rate
            )
        except Exception as e:
            logger.error(f"Error getting customer summary: {str(e)}")
            raise

    @staticmethod
    def get_customer_segments(db: Session) -> List[CustomerSegment]:
        """Get customer segments based on spending."""
        try:
            # Get all customers with their total spending
            customer_spending = db.query(
                Order.user_id,
                func.sum(Order.total_amount).label('total_spent'),
                func.count(Order.id).label('order_count')
            ).filter(
                Order.status != OrderStatus.CANCELLED.value
            ).group_by(
                Order.user_id
            ).all()
            
            if not customer_spending:
                return []
            
            # Define segments
            segments = {
                "VIP (>$1000)": {"min": 1000, "max": float('inf'), "customers": [], "total": 0},
                "Regular ($500-$1000)": {"min": 500, "max": 1000, "customers": [], "total": 0},
                "Occasional ($100-$500)": {"min": 100, "max": 500, "customers": [], "total": 0},
                "New (<$100)": {"min": 0, "max": 100, "customers": [], "total": 0},
            }
            
            for customer in customer_spending:
                spent = float(customer.total_spent or 0)
                for name, seg in segments.items():
                    if seg["min"] <= spent < seg["max"]:
                        seg["customers"].append(customer)
                        seg["total"] += spent
                        break
            
            total_customers = len(customer_spending)
            
            result = []
            for name, seg in segments.items():
                count = len(seg["customers"])
                if count > 0:
                    avg_order_count = sum(c.order_count for c in seg["customers"]) / count
                    result.append(CustomerSegment(
                        segment_name=name,
                        customer_count=count,
                        percentage=round((count / total_customers * 100), 2),
                        total_spent=round(seg["total"], 2),
                        average_order_value=round(seg["total"] / sum(c.order_count for c in seg["customers"]), 2) if seg["customers"] else 0
                    ))
            
            return result
        except Exception as e:
            logger.error(f"Error getting customer segments: {str(e)}")
            raise

    @staticmethod
    def get_top_customers(
        db: Session,
        start_date: datetime,
        end_date: datetime,
        limit: int = 10
    ) -> List[TopCustomer]:
        """Get top customers by spending."""
        try:
            results = db.query(
                User.id,
                User.first_name,
                User.last_name,
                User.email,
                func.count(Order.id).label('total_orders'),
                func.sum(Order.total_amount).label('total_spent'),
                func.min(Order.created_at).label('first_order'),
                func.max(Order.created_at).label('last_order')
            ).join(
                Order, User.id == Order.user_id
            ).filter(
                and_(
                    Order.created_at >= start_date,
                    Order.created_at <= end_date,
                    Order.status != OrderStatus.CANCELLED.value
                )
            ).group_by(
                User.id,
                User.first_name,
                User.last_name,
                User.email
            ).order_by(
                desc('total_spent')
            ).limit(limit).all()
            
            return [
                TopCustomer(
                    user_id=r.id,
                    customer_name=f"{r.first_name} {r.last_name}",
                    email=r.email,
                    total_orders=r.total_orders,
                    total_spent=float(r.total_spent or 0),
                    average_order_value=round(float(r.total_spent or 0) / r.total_orders if r.total_orders > 0 else 0, 2),
                    first_order_date=r.first_order,
                    last_order_date=r.last_order
                )
                for r in results
            ]
        except Exception as e:
            logger.error(f"Error getting top customers: {str(e)}")
            raise

    @staticmethod
    def get_customer_report(
        db: Session,
        date_range_type: DateRangeType = DateRangeType.LAST_30_DAYS,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 10
    ) -> CustomerReportResponse:
        """Generate complete customer report."""
        try:
            start_dt, end_dt = ReportService.get_date_range(date_range_type, start_date, end_date)
            
            return CustomerReportResponse(
                date_range={
                    "start": start_dt.strftime("%Y-%m-%d"),
                    "end": end_dt.strftime("%Y-%m-%d"),
                    "type": date_range_type.value
                },
                summary=ReportService.get_customer_summary(db, start_dt, end_dt),
                segments=ReportService.get_customer_segments(db),
                top_customers=ReportService.get_top_customers(db, start_dt, end_dt, limit),
                activity_trend=[]  # Implement if needed
            )
        except Exception as e:
            logger.error(f"Error generating customer report: {str(e)}")
            raise

    
    
    @staticmethod
    def get_analytics_dashboard(
        db: Session,
        date_range_type: DateRangeType = DateRangeType.LAST_30_DAYS,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> AnalyticsDashboardResponse:
        """Generate complete analytics dashboard."""
        try:
            start_dt, end_dt = ReportService.get_date_range(date_range_type, start_date, end_date)
            prev_start, prev_end = ReportService.get_previous_period(start_dt, end_dt)
            
            # Current period metrics
            current_summary = ReportService.get_sales_summary(db, start_dt, end_dt)
            prev_summary = ReportService.get_sales_summary(db, prev_start, prev_end)
            
            # Customer metrics
            current_new_customers = db.query(func.count(User.id)).filter(
                and_(User.created_at >= start_dt, User.created_at <= end_dt)
            ).scalar() or 0
            
            total_customers = db.query(func.count(User.id)).scalar() or 0
            
            # Calculate KPIs with growth rates
            kpi = KPIMetrics(
                total_revenue=current_summary.total_revenue,
                revenue_growth=ReportService.calculate_growth_rate(
                    current_summary.total_revenue, prev_summary.total_revenue
                ),
                total_orders=current_summary.total_orders,
                orders_growth=ReportService.calculate_growth_rate(
                    float(current_summary.total_orders), float(prev_summary.total_orders)
                ),
                average_order_value=current_summary.average_order_value,
                aov_growth=ReportService.calculate_growth_rate(
                    current_summary.average_order_value, prev_summary.average_order_value
                ),
                total_customers=total_customers,
                new_customers=current_new_customers,
                conversion_rate=0.0  # Implement with visit tracking if available
            )
            
            # Revenue breakdown
            revenue_breakdown = RevenueBreakdown(
                gross_revenue=current_summary.total_revenue,
                discounts=current_summary.total_discounts,
                refunds=0.0,  # Implement with payment tracking
                shipping_collected=current_summary.total_shipping,
                tax_collected=current_summary.total_tax,
                net_revenue=current_summary.net_revenue
            )
            
            # Order fulfillment
            total_orders = current_summary.total_orders
            delivered = current_summary.orders_delivered
            order_fulfillment = OrderFulfillment(
                pending_orders=current_summary.orders_pending,
                processing_orders=current_summary.orders_processing,
                shipped_orders=current_summary.orders_shipped,
                delivered_orders=delivered,
                cancelled_orders=current_summary.orders_cancelled,
                fulfillment_rate=round((delivered / total_orders * 100) if total_orders > 0 else 0, 2),
                average_fulfillment_time=None
            )
            
            # Payment metrics
            paid_amount = db.query(func.sum(Order.total_amount)).filter(
                and_(
                    Order.created_at >= start_dt,
                    Order.created_at <= end_dt,
                    Order.payment_status == PaymentStatus.PAID.value
                )
            ).scalar() or 0
            
            pending_amount = db.query(func.sum(Order.total_amount)).filter(
                and_(
                    Order.created_at >= start_dt,
                    Order.created_at <= end_dt,
                    Order.payment_status == PaymentStatus.PENDING.value
                )
            ).scalar() or 0
            
            failed_amount = db.query(func.sum(Order.total_amount)).filter(
                and_(
                    Order.created_at >= start_dt,
                    Order.created_at <= end_dt,
                    Order.payment_status == PaymentStatus.FAILED.value
                )
            ).scalar() or 0
            
            payment_metrics = PaymentMetrics(
                pending_amount=float(pending_amount),
                paid_amount=float(paid_amount),
                failed_amount=float(failed_amount),
                refunded_amount=0.0,
                success_rate=round(
                    (current_summary.payment_paid / total_orders * 100)
                    if total_orders > 0 else 0, 2
                )
            )
            
            # Get trend data
            daily_breakdown = ReportService.get_daily_sales_breakdown(db, start_dt, end_dt)
            sales_trend = [
                SalesTrendData(
                    period="day",
                    label=d.date.strftime("%Y-%m-%d"),
                    orders=d.orders_count,
                    revenue=d.revenue
                )
                for d in daily_breakdown
            ]
            
            return AnalyticsDashboardResponse(
                date_range={
                    "start": start_dt.strftime("%Y-%m-%d"),
                    "end": end_dt.strftime("%Y-%m-%d"),
                    "type": date_range_type.value
                },
                kpi=kpi,
                revenue_breakdown=revenue_breakdown,
                order_fulfillment=order_fulfillment,
                payment_metrics=payment_metrics,
                sales_trend=sales_trend,
                top_products=ReportService.get_top_selling_products(db, start_dt, end_dt, 5),
                sales_by_category=ReportService.get_sales_by_category(db, start_dt, end_dt)
            )
        except Exception as e:
            logger.error(f"Error generating analytics dashboard: {str(e)}")
            raise

    
    
    @staticmethod
    def get_quick_stats(db: Session) -> QuickStatsResponse:
        """Get quick stats for dashboard widgets."""
        try:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday = today - timedelta(days=1)
            
            # Today's metrics
            today_summary = ReportService.get_sales_summary(
                db, today, today.replace(hour=23, minute=59, second=59)
            )
            
            # Yesterday's metrics for comparison
            yesterday_summary = ReportService.get_sales_summary(
                db, yesterday, yesterday.replace(hour=23, minute=59, second=59)
            )
            
            # Pending orders
            pending_orders = db.query(func.count(Order.id)).filter(
                Order.status == OrderStatus.PENDING.value
            ).scalar() or 0
            
            # Low stock alerts
            low_stock_count = db.query(func.count(Inventory.id)).filter(
                (Inventory.stock_quantity - Inventory.reserved_quantity) <= Inventory.low_stock_threshold
            ).scalar() or 0
            
            # New customers today
            new_customers_today = db.query(func.count(User.id)).filter(
                User.created_at >= today
            ).scalar() or 0
            
            return QuickStatsResponse(
                today_revenue=today_summary.total_revenue,
                today_orders=today_summary.total_orders,
                pending_orders=pending_orders,
                low_stock_alerts=low_stock_count,
                new_customers_today=new_customers_today,
                compared_to_yesterday={
                    "revenue": ReportService.calculate_growth_rate(
                        today_summary.total_revenue, yesterday_summary.total_revenue
                    ),
                    "orders": ReportService.calculate_growth_rate(
                        float(today_summary.total_orders), float(yesterday_summary.total_orders)
                    )
                }
            )
        except Exception as e:
            logger.error(f"Error getting quick stats: {str(e)}")
            raise

    
    @staticmethod
    def export_to_csv(data: List[Dict], filename: str) -> Tuple[bytes, str]:
        """Export data to CSV format."""
        try:
            if not data:
                return b"", filename
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            
            return output.getvalue().encode('utf-8'), f"{filename}.csv"
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            raise

    @staticmethod
    def export_sales_report(
        db: Session,
        date_range_type: DateRangeType = DateRangeType.LAST_30_DAYS,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        format: ExportFormat = ExportFormat.CSV
    ) -> Tuple[bytes, str]:
        """Export sales report to file."""
        try:
            start_dt, end_dt = ReportService.get_date_range(date_range_type, start_date, end_date)
            
            # Get orders
            orders = db.query(Order).filter(
                and_(
                    Order.created_at >= start_dt,
                    Order.created_at <= end_dt
                )
            ).all()
            
            data = [
                {
                    "order_number": o.order_number,
                    "date": o.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": o.status,
                    "payment_status": o.payment_status,
                    "subtotal": float(o.subtotal),
                    "tax": float(o.tax_amount),
                    "shipping": float(o.shipping_amount),
                    "discount": float(o.discount_amount),
                    "total": float(o.total_amount)
                }
                for o in orders
            ]
            
            filename = f"sales_report_{start_dt.strftime('%Y%m%d')}_{end_dt.strftime('%Y%m%d')}"
            
            return ReportService.export_to_csv(data, filename)
        except Exception as e:
            logger.error(f"Error exporting sales report: {str(e)}")
            raise

    @staticmethod
    def export_inventory_report(
        db: Session,
        format: ExportFormat = ExportFormat.CSV
    ) -> Tuple[bytes, str]:
        """Export inventory report to file."""
        try:
            items = ReportService.get_inventory_items(db, limit=1000)
            
            data = [
                {
                    "product_name": i.product_name,
                    "variant_name": i.variant_name or "",
                    "sku": i.sku or "",
                    "stock_quantity": i.stock_quantity,
                    "reserved_quantity": i.reserved_quantity,
                    "available_quantity": i.available_quantity,
                    "low_stock_threshold": i.low_stock_threshold,
                    "reorder_level": i.reorder_level,
                    "location": i.location or "",
                    "status": i.status
                }
                for i in items
            ]
            
            filename = f"inventory_report_{datetime.now().strftime('%Y%m%d')}"
            
            return ReportService.export_to_csv(data, filename)
        except Exception as e:
            logger.error(f"Error exporting inventory report: {str(e)}")
            raise

    @staticmethod
    def export_customer_report(
        db: Session,
        date_range_type: DateRangeType = DateRangeType.LAST_30_DAYS,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        format: ExportFormat = ExportFormat.CSV
    ) -> Tuple[bytes, str]:
        """Export customer report to file."""
        try:
            start_dt, end_dt = ReportService.get_date_range(date_range_type, start_date, end_date)
            
            top_customers = ReportService.get_top_customers(db, start_dt, end_dt, 100)
            
            data = [
                {
                    "customer_name": c.customer_name,
                    "email": c.email,
                    "total_orders": c.total_orders,
                    "total_spent": c.total_spent,
                    "average_order_value": c.average_order_value,
                    "first_order_date": c.first_order_date.strftime("%Y-%m-%d") if c.first_order_date else "",
                    "last_order_date": c.last_order_date.strftime("%Y-%m-%d") if c.last_order_date else ""
                }
                for c in top_customers
            ]
            
            filename = f"customer_report_{start_dt.strftime('%Y%m%d')}_{end_dt.strftime('%Y%m%d')}"
            
            return ReportService.export_to_csv(data, filename)
        except Exception as e:
            logger.error(f"Error exporting customer report: {str(e)}")
            raise
