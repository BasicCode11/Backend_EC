import httpx
import logging
from typing import Optional, Dict, Any
from app.core.config import settings
from datetime import datetime


logger = logging.getLogger(__name__)


class TelegramService:
    """
    Service for sending messages via Telegram Bot API.
    Uses httpx for async/sync HTTP requests.
    """

    @staticmethod
    def is_configured() -> bool:
        """Check if Telegram is properly configured"""
        return bool(
            settings.TELEGRAM_ALERTS_ENABLED
            and settings.TELEGRAM_BOT_TOKEN
            and settings.TELEGRAM_CHAT_ID
        )

    @staticmethod
    def send_message(
        message: str,
        parse_mode: str = "HTML",
        disable_notification: bool = False
    ) -> Dict[str, Any]:
        """
        Send a message via Telegram Bot API.

        Args:
            message: Message text to send (supports HTML or Markdown)
            parse_mode: Message parse mode ("HTML" or "Markdown")
            disable_notification: Send silently without notification

        Returns:
            dict: Response from Telegram API

        Raises:
            Exception: If Telegram is not configured or request fails
        """
        if not TelegramService.is_configured():
            logger.warning("⚠️ Telegram alerts are not configured or disabled")
            return {
                "ok": False,
                "error": "Telegram not configured. Set TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, and TELEGRAM_ALERTS_ENABLED=true"
            }

        try:
            bot_token = settings.TELEGRAM_BOT_TOKEN
            chat_id = settings.TELEGRAM_CHAT_ID

            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": parse_mode,
                "disable_notification": disable_notification
            }

            logger.info("=" * 80)
            logger.info(f"[TELEGRAM] Sending message to chat_id: {chat_id}")
            logger.info(f"[TELEGRAM] Message:\n{message}")
            logger.info("=" * 80)

            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()

            if result.get("ok"):
                logger.info(f"✅ Telegram message sent successfully")
                return result
            else:
                logger.error(f"❌ Telegram API returned error: {result}")
                return result

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Telegram HTTP error: {e.response.status_code} - {e.response.text}")
            return {
                "ok": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}"
            }
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram message: {str(e)}")
            return {
                "ok": False,
                "error": str(e)
            }

    @staticmethod
    async def send_message_async(
        message: str,
        parse_mode: str = "HTML",
        disable_notification: bool = False
    ) -> Dict[str, Any]:
        """
        Send a message via Telegram Bot API (async version).

        Args:
            message: Message text to send (supports HTML or Markdown)
            parse_mode: Message parse mode ("HTML" or "Markdown")
            disable_notification: Send silently without notification

        Returns:
            dict: Response from Telegram API
        """
        if not TelegramService.is_configured():
            logger.warning("⚠️ Telegram alerts are not configured or disabled")
            return {
                "ok": False,
                "error": "Telegram not configured"
            }

        try:
            bot_token = settings.TELEGRAM_BOT_TOKEN
            chat_id = settings.TELEGRAM_CHAT_ID

            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": parse_mode,
                "disable_notification": disable_notification
            }

            logger.info(f"[TELEGRAM] Sending async message to chat_id: {chat_id}")

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()

            if result.get("ok"):
                logger.info(f"✅ Telegram message sent successfully (async)")
                return result
            else:
                logger.error(f"❌ Telegram API returned error: {result}")
                return result

        except Exception as e:
            logger.error(f"❌ Failed to send Telegram message (async): {str(e)}")
            return {
                "ok": False,
                "error": str(e)
            }

    @staticmethod
    def format_low_stock_alert(items):
        if not items:
            return "No low stock items."

        message = "🚨 LOW STOCK ALERT 🚨\n\n"
        message += f"⚠️ {len(items)} product(s) need attention:\n\n"

        for idx, item in enumerate(items, start=1):
            product_name = item.product.name if item.product else "Unknown Product"
            location = item.location if item.location else "Unknown Location"
            sku = item.sku if item.sku else "N/A"

            message += (
                f"{idx}. {product_name}\n"
                f"   📦 Available: {item.available_quantity} units\n"
                f"   ⚠️ Threshold: {item.low_stock_threshold} units\n"
                f"   📍 Location: {location}\n"
                f"   🔖 SKU: {sku}\n\n"
            )

        message += "⏰ Please reorder these items soon!\n\n"
        message += f"🕐 Alert sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return message

    @staticmethod
    def format_reorder_alert(inventory_items: list) -> str:
        """
        Format items needing reorder into a Telegram message.

        Args:
            inventory_items: List of inventory items needing reorder

        Returns:
            str: Formatted HTML message
        """
        if not inventory_items:
            return "✅ <b>No items need immediate reordering!</b>"

        message_lines = [
            "🔴 <b>URGENT REORDER REQUIRED</b> 🔴",
            "",
            f"🚨 <b>{len(inventory_items)} product(s) reached reorder level:</b>",
            ""
        ]

        for idx, item in enumerate(inventory_items, 1):
            product_name = item.product.name if item.product else "Unknown Product"
            available = item.available_quantity
            reorder_level = item.reorder_level
            location = item.location or "N/A"
            sku = item.sku or "N/A"

            message_lines.append(f"<b>{idx}. {product_name}</b>")
            message_lines.append(f"   📦 Available: <b>{available}</b> units")
            message_lines.append(f"   🔴 Reorder Level: {reorder_level} units")
            message_lines.append(f"   📍 Location: {location}")
            message_lines.append(f"   🔖 SKU: {sku}")
            message_lines.append("")

        message_lines.append("🚨 <b>ACTION REQUIRED: Place orders immediately!</b>")
        message_lines.append("")
        message_lines.append(f"🕐 Alert sent at: {TelegramService._get_current_time()}")

        return "\n".join(message_lines)

    @staticmethod
    def format_out_of_stock_alert(inventory_items: list) -> str:
        """
        Format out-of-stock items into a Telegram message.

        Args:
            inventory_items: List of inventory items that are out of stock

        Returns:
            str: Formatted HTML message
        """
        if not inventory_items:
            return "✅ <b>All items are in stock!</b>"

        message_lines = [
            "⛔ <b>OUT OF STOCK ALERT</b> ⛔",
            "",
            f"❌ <b>{len(inventory_items)} product(s) are out of stock:</b>",
            ""
        ]

        for idx, item in enumerate(inventory_items, 1):
            product_name = item.product.name if item.product else "Unknown Product"
            reserved = item.reserved_quantity
            location = item.location or "N/A"
            sku = item.sku or "N/A"

            message_lines.append(f"<b>{idx}. {product_name}</b>")
            message_lines.append(f"   ❌ Stock: <b>0</b> units")
            if reserved > 0:
                message_lines.append(f"   ⚠️ Reserved: {reserved} units (pending orders)")
            message_lines.append(f"   📍 Location: {location}")
            message_lines.append(f"   🔖 SKU: {sku}")
            message_lines.append("")

        message_lines.append("⚠️ <b>These products cannot be sold until restocked!</b>")
        message_lines.append("")
        message_lines.append(f"🕐 Alert sent at: {TelegramService._get_current_time()}")

        return "\n".join(message_lines)

    @staticmethod
    def format_inventory_summary(stats: dict) -> str:
        """
        Format inventory statistics into a Telegram message.

        Args:
            stats: Dictionary containing inventory statistics

        Returns:
            str: Formatted HTML message
        """
        message_lines = [
            "📊 <b>INVENTORY SUMMARY REPORT</b> 📊",
            "",
            "<b>Overall Statistics:</b>",
            f"📦 Total Products: <b>{stats.get('total_products', 0)}</b>",
            f"📈 Total Stock: <b>{stats.get('total_stock', 0)}</b> units",
            f"🔒 Reserved Stock: <b>{stats.get('total_reserved', 0)}</b> units",
            f"✅ Available Stock: <b>{stats.get('total_available', 0)}</b> units",
            "",
            "<b>Alerts:</b>",
            f"⚠️ Low Stock Items: <b>{stats.get('low_stock_count', 0)}</b>",
            f"🔴 Need Reorder: <b>{stats.get('needs_reorder_count', 0)}</b>",
            f"❌ Out of Stock: <b>{stats.get('out_of_stock_count', 0)}</b>",
            f"⏰ Expired Items: <b>{stats.get('expired_count', 0)}</b>",
            "",
            f"🕐 Report generated at: {TelegramService._get_current_time()}"
        ]

        return "\n".join(message_lines)

    @staticmethod
    def format_expiry_soon_alert(items: list, days_threshold: int) -> str:
        """
        Format items expiring soon into a Telegram message.
        """
        if not items:
            return f"✅ <b>No items are expiring in the next {days_threshold} days.</b>"

        message_lines = [
            f"⏳ <b>EXPIRY SOON ALERT ({days_threshold} DAYS)</b> ⏳",
            "",
            f"Heads up! <b>{len(items)} item(s)</b> are expiring soon:",
            ""
        ]

        for idx, item in enumerate(items, 1):
            product_name = item.variant.product.name if item.variant and hasattr(item.variant, 'product') and item.variant.product else "Unknown Product"
            variant_name = f" ({item.variant.variant_name})" if item.variant and item.variant.variant_name else ""
            sku = item.sku or "N/A"
            expiry_date_str = item.expiry_date.strftime("%Y-%m-%d") if item.expiry_date else "N/A"
            days_left_val = (item.expiry_date - datetime.now(item.expiry_date.tzinfo)).days if item.expiry_date else 'N/A'


            message_lines.append(f"<b>{idx}. {product_name}{variant_name}</b>")
            message_lines.append(f"   🗓️ Expires on: <b>{expiry_date_str}</b> ({days_left_val} days left)")
            message_lines.append(f"   📦 Stock: {item.available_quantity} units")
            message_lines.append(f"   🔖 SKU: {sku}")
            message_lines.append("")

        message_lines.append("ACTION: Prioritize selling these items!")
        message_lines.append("")
        message_lines.append(f"🕐 Alert sent at: {TelegramService._get_current_time()}")

        return "\n".join(message_lines)

    @staticmethod
    def _get_current_time() -> str:
        """Get current time as formatted string"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def test_connection() -> Dict[str, Any]:
        """
        Test Telegram bot connection by sending a test message.

        Returns:
            dict: Result of the test
        """
        if not TelegramService.is_configured():
            return {
                "ok": False,
                "message": "Telegram is not configured. Please set TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, and enable TELEGRAM_ALERTS_ENABLED"
            }

        test_message = "🤖 <b>Test Message</b>\n\n✅ Your Telegram bot is configured correctly!"
        result = TelegramService.send_message(test_message)

        if result.get("ok"):
            return {
                "ok": True,
                "message": "Telegram connection successful! Check your Telegram chat for the test message."
            }
        else:
            return {
                "ok": False,
                "message": f"Failed to send test message: {result.get('error', 'Unknown error')}"
            }
