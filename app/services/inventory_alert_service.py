from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime
from app.services.inventory_service import InventoryService
from app.services.telegram_service import TelegramService
from app.services.audit_log_service import AuditLogService
from app.models.user import User
from app.models.inventory import Inventory
import logging

logger = logging.getLogger(__name__)


class InventoryAlertService:
    """
    Service for sending inventory-related alerts via Telegram.
    Includes low stock, reorder, out-of-stock, and summary alerts.
    """

    # =========================
    # 📦 LOW STOCK ALERT
    # =========================
    @staticmethod
    def send_low_stock_alerts(db: Session, current_user: User = None) -> Dict[str, Any]:
        """Send Telegram alerts for low stock items."""
        try:
            # Get low stock items
            low_stock_items = InventoryService.get_low_stock_items(db)

            if not low_stock_items:
                logger.info("No low stock items found")
                return {"success": True, "message": "No low stock items", "count": 0}

            # Build Telegram message
            message_lines = ["🚨 LOW STOCK ALERT 🚨", "", f"⚠️ {len(low_stock_items)} product(s) need attention:", ""]
            for idx, item in enumerate(low_stock_items, start=1):
                product_name = item.product.name if item.product else f"Product #{item.product_id}"
                message_lines.append(
                    f"{idx}. {product_name}\n"
                    f"   📦 Available: {item.available_quantity} units\n"
                    f"   ⚠️ Threshold: {item.low_stock_threshold} units\n"
                    f"   📍 Location: {item.location or 'N/A'}\n"
                    f"   🔖 SKU: {item.sku or 'N/A'}\n"
                )
            message_lines.append("⏰ Please reorder these items soon!")
            message_lines.append(f"\n🕐 Alert sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            message = "\n".join(message_lines)
            telegram_result = TelegramService.send_message(message)



            return {
                "success": telegram_result.get("ok", False),
                "message": "Low stock alert sent successfully" if telegram_result.get("ok")
                else f"Failed to send alert: {telegram_result.get('error')}",
                "count": len(low_stock_items),
                "items": [
                    {
                        "id": item.id,
                        "product_name": item.product.name if item.product else f"Product #{item.product_id}",
                        "available_quantity": item.available_quantity,
                        "low_stock_threshold": item.low_stock_threshold,
                        "location": item.location,
                    }
                    for item in low_stock_items
                ],
                "telegram_response": telegram_result
            }

        except Exception as e:
            logger.error(f"Error sending low stock alert: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}


    # =========================
    # 🔁 REORDER ALERT
    # =========================
    @staticmethod
    def send_reorder_alerts(db: Session, current_user: User = None) -> Dict[str, Any]:
        """Send Telegram alerts for items needing reorder."""
        try:
            reorder_items = InventoryService.get_reorder_items(db)
            if not reorder_items:
                logger.info("No reorder items found")
                return {"success": True, "message": "No items need reordering", "count": 0}

            message = TelegramService.format_reorder_alert(reorder_items)
            telegram_result = TelegramService.send_message(message)

            if current_user:
                AuditLogService.log_action(
                    db=db,
                    user_id=current_user.id,
                    action="REORDER_ALERT",
                    resource_type="Inventory",
                    details=f"Reorder alert sent for {len(reorder_items)} items",
                )

            return {
                "success": telegram_result.get("ok", False),
                "message": "Reorder alert sent successfully"
                if telegram_result.get("ok")
                else f"Failed to send alert: {telegram_result.get('error')}",
                "count": len(reorder_items),
                "items": [
                    {
                        "id": item.id,
                        "product_name": item.product.name if item.product else "Unknown",
                        "available_quantity": item.available_quantity,
                        "reorder_level": item.reorder_level,
                        "location": item.location,
                    }
                    for item in reorder_items
                ],
            }

        except Exception as e:
            logger.error(f"Error sending reorder alert: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}

    # =========================
    # ❌ OUT OF STOCK ALERT
    # =========================
    @staticmethod
    def send_out_of_stock_alerts(db: Session, current_user: User = None) -> Dict[str, Any]:
        """Send Telegram alerts for out-of-stock items."""
        try:
            query = select(Inventory).where(
                (Inventory.stock_quantity - Inventory.reserved_quantity) <= 0
            )
            out_of_stock_items = db.execute(query).scalars().all()

            if not out_of_stock_items:
                logger.info("No out-of-stock items found")
                return {"success": True, "message": "No out-of-stock items", "count": 0}

            message = TelegramService.format_out_of_stock_alert(out_of_stock_items)
            telegram_result = TelegramService.send_message(message)

            if current_user:
                AuditLogService.log_action(
                    db=db,
                    user_id=current_user.id,
                    action="OUT_OF_STOCK_ALERT",
                    resource_type="Inventory",
                    details=f"Out-of-stock alert sent for {len(out_of_stock_items)} items",
                )

            return {
                "success": telegram_result.get("ok", False),
                "message": "Out-of-stock alert sent successfully"
                if telegram_result.get("ok")
                else f"Failed to send alert: {telegram_result.get('error')}",
                "count": len(out_of_stock_items),
                "items": [
                    {
                        "id": item.id,
                        "product_name": item.product.name if item.product else "Unknown",
                        "stock_quantity": item.stock_quantity,
                        "reserved_quantity": item.reserved_quantity,
                        "location": item.location,
                    }
                    for item in out_of_stock_items
                ],
            }

        except Exception as e:
            logger.error(f"Error sending out-of-stock alert: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}

    # =========================
    # 📊 INVENTORY SUMMARY
    # =========================
    @staticmethod
    def send_inventory_summary(db: Session, current_user: User = None) -> Dict[str, Any]:
        """Send an overall inventory summary."""
        try:
            stats = InventoryService.get_statistics(db)
            message = TelegramService.format_inventory_summary(stats)
            telegram_result = TelegramService.send_message(message)

            if current_user:
                AuditLogService.log_action(
                    db=db,
                    user_id=current_user.id,
                    action="INVENTORY_SUMMARY",
                    resource_type="Inventory",
                    details="Inventory summary report sent",
                )

            return {
                "success": telegram_result.get("ok", False),
                "message": "Inventory summary sent successfully"
                if telegram_result.get("ok")
                else f"Failed to send summary: {telegram_result.get('error')}",
                "statistics": stats,
            }

        except Exception as e:
            logger.error(f"Error sending inventory summary: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}

    # =========================
    # 🗓️ DAILY REPORT
    # =========================
    @staticmethod
    def send_daily_report(db: Session) -> Dict[str, Any]:
        """Send a daily inventory report that includes all alert types."""
        try:
            results = {
                "summary": InventoryAlertService.send_inventory_summary(db),
                "low_stock": InventoryAlertService.send_low_stock_alerts(db),
                "reorder": InventoryAlertService.send_reorder_alerts(db),
                "out_of_stock": InventoryAlertService.send_out_of_stock_alerts(db),
            }

            return {"success": True, "message": "Daily inventory report sent", "results": results}

        except Exception as e:
            logger.error(f"Error sending daily report: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}

    # =========================
    # ✉️ CUSTOM ALERT
    # =========================
    @staticmethod
    def send_custom_alert(db: Session, message: str, current_user: User = None) -> Dict[str, Any]:
        """Send a custom Telegram alert."""
        try:
            telegram_result = TelegramService.send_message(message)

            if current_user:
                AuditLogService.log_action(
                    db=db,
                    user_id=current_user.id,
                    action="CUSTOM_ALERT",
                    resource_type="Inventory",
                    details="Custom alert message sent",
                )

            return {
                "success": telegram_result.get("ok", False),
                "message": "Custom alert sent successfully"
                if telegram_result.get("ok")
                else f"Failed to send alert: {telegram_result.get('error')}",
            }

        except Exception as e:
            logger.error(f"Error sending custom alert: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}
