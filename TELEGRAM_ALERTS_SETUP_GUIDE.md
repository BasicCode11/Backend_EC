# Telegram Alerts Setup Guide

## Overview
This guide will help you set up Telegram notifications for low stock alerts in your e-commerce inventory system. When products fall below their low stock threshold, you'll receive instant notifications on Telegram.

---

## 🚀 Quick Setup (5 Steps)

### Step 1: Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Start a chat and send: `/newbot`
3. Follow the prompts:
   - Choose a name for your bot (e.g., "My Store Inventory Bot")
   - Choose a username (must end with 'bot', e.g., "mystore_inventory_bot")
4. **Save the Bot Token** - You'll receive something like:
   ```
   123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

### Step 2: Get Your Chat ID

**Option A: Using Your Bot**
1. Start a chat with your newly created bot
2. Send any message to the bot (e.g., "Hello")
3. Open this URL in your browser (replace `YOUR_BOT_TOKEN`):
   ```
   https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
   ```
4. Look for `"chat":{"id":` in the response - this is your Chat ID
   - Example: `"chat":{"id":123456789,`
   - Your Chat ID is: `123456789`

**Option B: Using @userinfobot**
1. Search for **@userinfobot** in Telegram
2. Start a chat and send any message
3. The bot will reply with your Chat ID

**For Groups:**
1. Add your bot to a group
2. Send a message in the group mentioning the bot
3. Use the getUpdates URL from Option A
4. The Chat ID will be negative (e.g., `-987654321`)

### Step 3: Configure Environment Variables

Add these lines to your `.env` file:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
TELEGRAM_ALERTS_ENABLED=true
```

Replace with your actual values from Steps 1 and 2.

### Step 4: Install Dependencies

```bash
pip install httpx==0.27.0
```

Or install from requirements.txt:
```bash
pip install -r requirements.txt
```

### Step 5: Test Your Setup

**Using the API:**
```bash
# Start your FastAPI server
uvicorn main:app --reload

# Test Telegram connection (in another terminal or via browser)
curl -X GET "http://localhost:8000/api/inventory/alerts/test-telegram" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Using Swagger UI:**
1. Go to `http://localhost:8000/docs`
2. Find `/api/inventory/alerts/test-telegram`
3. Click "Try it out" → "Execute"
4. Check your Telegram for the test message!

✅ If you receive a test message, you're all set!

---

## 📱 Available Alert Endpoints

### 1. Test Connection
```http
GET /api/inventory/alerts/test-telegram
```
**Purpose**: Verify Telegram bot is working
**Response**: Sends a test message to Telegram

### 2. Low Stock Alert
```http
POST /api/inventory/alerts/low-stock
```
**Purpose**: Alert for items below low_stock_threshold
**Example Message**:
```
🚨 LOW STOCK ALERT 🚨

⚠️ 3 product(s) need attention:

1. iPhone 14 Pro
   📦 Available: 8 units
   ⚠️ Threshold: 10 units
   📍 Location: Warehouse A
   🔖 SKU: PHONE-001

2. MacBook Pro M2
   📦 Available: 3 units
   ⚠️ Threshold: 5 units
   📍 Location: Main Store
   🔖 SKU: LAPTOP-002
```

### 3. Reorder Alert
```http
POST /api/inventory/alerts/reorder
```
**Purpose**: Alert for items at reorder_level (urgent)
**Use Case**: Items need immediate ordering

### 4. Out of Stock Alert
```http
POST /api/inventory/alerts/out-of-stock
```
**Purpose**: Alert for items with 0 available stock
**Use Case**: Items cannot be sold

### 5. Inventory Summary
```http
POST /api/inventory/alerts/summary
```
**Purpose**: Send comprehensive inventory statistics
**Example Message**:
```
📊 INVENTORY SUMMARY REPORT 📊

Overall Statistics:
📦 Total Products: 150
📈 Total Stock: 5000 units
🔒 Reserved Stock: 250 units
✅ Available Stock: 4750 units

Alerts:
⚠️ Low Stock Items: 12
🔴 Need Reorder: 5
❌ Out of Stock: 3
⏰ Expired Items: 2
```

### 6. Daily Report
```http
POST /api/inventory/alerts/daily-report
```
**Purpose**: Send all alerts in one comprehensive report
**Includes**: Summary + Low Stock + Reorder + Out of Stock alerts

### 7. Custom Alert
```http
POST /api/inventory/alerts/custom
Content-Type: application/json

{
  "message": "🎉 <b>Special Announcement</b>\n\nNew inventory arrived today!"
}
```
**Purpose**: Send custom messages to Telegram
**Supports**: HTML formatting

---

## 🤖 Usage Examples

### Example 1: Manual Low Stock Check
```bash
curl -X POST "http://localhost:8000/api/inventory/alerts/low-stock" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

### Example 2: Daily Report
```bash
curl -X POST "http://localhost:8000/api/inventory/alerts/daily-report" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Example 3: Custom Alert
```bash
curl -X POST "http://localhost:8000/api/inventory/alerts/custom" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "🚨 <b>Emergency</b>: Check inventory system!"}'
```

### Example 4: Using Python
```python
import requests

API_URL = "http://localhost:8000/api"
TOKEN = "your_access_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Send low stock alert
response = requests.post(
    f"{API_URL}/inventory/alerts/low-stock",
    headers=headers
)

print(response.json())
```

---

## ⏰ Automated Alerts (Scheduled Tasks)

### Option 1: Using Cron (Linux/Mac)
```bash
# Edit crontab
crontab -e

# Add these lines:

# Daily report at 9 AM
0 9 * * * curl -X POST "http://localhost:8000/api/inventory/alerts/daily-report" -H "Authorization: Bearer YOUR_TOKEN"

# Low stock check every 6 hours
0 */6 * * * curl -X POST "http://localhost:8000/api/inventory/alerts/low-stock" -H "Authorization: Bearer YOUR_TOKEN"

# Reorder check daily at 8 AM
0 8 * * * curl -X POST "http://localhost:8000/api/inventory/alerts/reorder" -H "Authorization: Bearer YOUR_TOKEN"
```

### Option 2: Using Task Scheduler (Windows)
1. Open Task Scheduler
2. Create New Task
3. Set Trigger: Daily at 9:00 AM
4. Set Action: Start a program
   - Program: `curl.exe`
   - Arguments: `-X POST "http://localhost:8000/api/inventory/alerts/daily-report" -H "Authorization: Bearer YOUR_TOKEN"`

### Option 3: Using Python APScheduler
```python
from apscheduler.schedulers.background import BackgroundScheduler
import requests

def send_daily_report():
    requests.post(
        "http://localhost:8000/api/inventory/alerts/daily-report",
        headers={"Authorization": "Bearer YOUR_TOKEN"}
    )

scheduler = BackgroundScheduler()
scheduler.add_job(send_daily_report, 'cron', hour=9)  # Daily at 9 AM
scheduler.start()
```

### Option 4: Using FastAPI Background Tasks (Recommended)

Create a background task in your FastAPI app:

```python
# In your main.py or a new file
from fastapi import BackgroundTasks
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.inventory_alert_service import InventoryAlertService
from app.database import SessionLocal

async def scheduled_low_stock_check():
    db = SessionLocal()
    try:
        InventoryAlertService.send_low_stock_alerts(db)
    finally:
        db.close()

# In lifespan or startup event
@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    # Daily at 9 AM
    scheduler.add_job(scheduled_low_stock_check, 'cron', hour=9)
    scheduler.start()
    
    yield
    
    scheduler.shutdown()
```

---

## 🎨 Message Formatting

Telegram supports HTML formatting:

```python
# Bold text
<b>Bold Text</b>

# Italic text
<i>Italic Text</i>

# Underline
<u>Underlined Text</u>

# Code
<code>code snippet</code>

# Links
<a href="http://example.com">Link Text</a>

# Combined
<b>Product:</b> <i>iPhone 14</i>
<code>SKU: PHONE-001</code>
```

---

## 🔧 Troubleshooting

### Problem: "Telegram not configured" error
**Solution**: 
- Check `.env` file has all three variables set
- Verify `TELEGRAM_ALERTS_ENABLED=true`
- Restart your FastAPI server after changing .env

### Problem: "HTTP 401 Unauthorized"
**Solution**:
- Your bot token is incorrect
- Get a new token from @BotFather

### Problem: "HTTP 400 Bad Request: chat not found"
**Solution**:
- Your Chat ID is incorrect
- Make sure you've started a chat with your bot first
- For groups, ensure the Chat ID is negative

### Problem: Bot doesn't respond
**Solution**:
- Check bot token is correct
- Verify your bot hasn't been blocked
- Test with @BotFather to ensure bot is active

### Problem: No alerts received
**Solution**:
- Check `TELEGRAM_ALERTS_ENABLED=true` in .env
- Verify there are actually low stock items: `GET /api/inventory/low-stock`
- Check application logs for errors

### Problem: "Module 'httpx' not found"
**Solution**:
```bash
pip install httpx==0.27.0
```

---

## 🔐 Security Best Practices

1. **Keep Bot Token Secret**
   - Never commit `.env` to git
   - Use `.env.example` for templates
   - Rotate tokens periodically

2. **Use Private Chats or Groups**
   - Don't post sensitive inventory data to public channels
   - Use private groups for team notifications

3. **Implement Rate Limiting**
   - Don't spam alerts
   - Use scheduled tasks instead of real-time for every change

4. **Access Control**
   - Only authorized users should trigger manual alerts
   - Use FastAPI dependencies for authentication

---

## 📊 Alert Workflow Recommendations

### 1. Morning Routine (9 AM)
```
Daily Report → Review all statistics
```

### 2. Every 6 Hours
```
Low Stock Check → Identify items needing attention
```

### 3. Daily Evening (8 PM)
```
Reorder Check → Place orders for critical items
```

### 4. Real-Time Triggers
```
Out of Stock → Immediate alert when item reaches 0
```

---

## 🌟 Advanced Features

### Sending Alerts to Multiple Chats

Modify the Telegram service to support multiple chat IDs:

```python
# In .env
TELEGRAM_CHAT_IDS=123456789,987654321,-111222333

# Update telegram_service.py to loop through IDs
```

### Custom Alert Conditions

Create custom endpoints for specific conditions:

```python
@router.post("/inventory/alerts/high-value-low-stock")
def alert_high_value_products(db: Session):
    # Alert only for products with high value and low stock
    items = db.query(Inventory).join(Product).filter(
        Inventory.available_quantity <= Inventory.low_stock_threshold,
        Product.price > 1000  # High value products
    ).all()
    # Send alert...
```

### Integration with Other Systems

```python
# Example: Alert when order cannot be fulfilled
def process_order(order_id, product_id, quantity):
    inventory = get_inventory(product_id)
    if inventory.available_quantity < quantity:
        # Send Telegram alert
        TelegramService.send_message(
            f"⚠️ Order #{order_id} cannot be fulfilled\n"
            f"Product: {inventory.product.name}\n"
            f"Requested: {quantity}, Available: {inventory.available_quantity}"
        )
```

---

## 📞 Support

If you encounter issues:

1. Check FastAPI logs: Look for `[TELEGRAM]` prefix messages
2. Test the bot manually: Send message directly via Telegram
3. Verify environment variables are loaded: `print(settings.TELEGRAM_BOT_TOKEN)`
4. Use the test endpoint: `/api/inventory/alerts/test-telegram`

---

## 📝 Summary

You now have a complete Telegram alert system that can:
- ✅ Send low stock alerts
- ✅ Send reorder notifications  
- ✅ Alert on out-of-stock items
- ✅ Provide inventory summaries
- ✅ Send custom messages
- ✅ Generate daily reports

**Next Steps:**
1. Set up automated scheduling (cron or APScheduler)
2. Customize alert thresholds for each product
3. Create team channels for different departments
4. Integrate with your order processing system

Happy alerting! 🎉
