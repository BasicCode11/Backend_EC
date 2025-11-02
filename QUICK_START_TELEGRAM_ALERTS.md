# 🚀 Quick Start: Telegram Low Stock Alerts

## Setup in 5 Minutes

### Step 1: Create Your Bot (2 minutes)

1. Open **Telegram** on your phone or computer
2. Search for: `@BotFather`
3. Send: `/start`
4. Send: `/newbot`
5. Choose a name: `My Store Alerts` (or any name)
6. Choose username: `mystore_alerts_bot` (must end with `_bot`)
7. **Copy the token** you receive:
   ```
   Example: 6789012345:AAGHdksjfhSDKFHkjshdfKJHSDKJFhsdkj
   ```

### Step 2: Get Your Chat ID (1 minute)

1. **Start a chat** with your new bot (search for your bot username)
2. Send any message like: `hello`
3. Open this URL in your browser (replace with your token):
   ```
   https://api.telegram.org/bot6789012345:AAGHdksjfhSDKFHkjshdfKJHSDKJFhsdkj/getUpdates
   ```
4. Find your Chat ID in the response:
   ```json
   "chat":{"id":1234567890,
   ```
   Your Chat ID is: `1234567890`

### Step 3: Configure Your App (1 minute)

Open your `.env` file and add:

```env
TELEGRAM_BOT_TOKEN=6789012345:AAGHdksjfhSDKFHkjshdfKJHSDKJFhsdkj
TELEGRAM_CHAT_ID=1234567890
TELEGRAM_ALERTS_ENABLED=true
```

### Step 4: Install Package (30 seconds)

```bash
pip install httpx==0.27.0
```

### Step 5: Test It! (30 seconds)

```bash
# Start your server
uvicorn main:app --reload

# In another terminal or browser, go to:
# http://localhost:8000/docs

# Find: GET /api/inventory/alerts/test-telegram
# Click "Try it out" → "Execute"
```

✅ **Check your Telegram!** You should receive a test message.

---

## 📱 Send Your First Alert

### Using Browser (Swagger UI)

1. Go to: `http://localhost:8000/docs`
2. Find: `POST /api/inventory/alerts/low-stock`
3. Click **"Try it out"**
4. Click **"Execute"**
5. Check your Telegram! 🎉

### Using Command Line

```bash
# Replace YOUR_TOKEN with your actual access token
curl -X POST "http://localhost:8000/api/inventory/alerts/low-stock" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Using Python

```python
import requests

response = requests.post(
    "http://localhost:8000/api/inventory/alerts/low-stock",
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

print(response.json())
```

---

## 🔥 What You Get

### Low Stock Alert Message

When you call `/api/inventory/alerts/low-stock`:

```
🚨 LOW STOCK ALERT 🚨

⚠️ 3 product(s) need attention:

1. iPhone 14 Pro
   📦 Available: 8 units
   ⚠️ Threshold: 10 units
   📍 Location: Warehouse A
   🔖 SKU: PHONE-001

2. Samsung Galaxy S23
   📦 Available: 4 units
   ⚠️ Threshold: 10 units
   📍 Location: Main Store
   🔖 SKU: PHONE-002

⏰ Please reorder these items soon!
🕐 Alert sent at: 2025-11-02 10:30:00
```

---

## ⏰ Automate Daily Alerts

### Option 1: Windows Task Scheduler

1. Open **Task Scheduler**
2. Create **New Task**
3. **Trigger:** Daily at 9:00 AM
4. **Action:** Start a program
   - Program: `curl.exe`
   - Arguments: `-X POST "http://localhost:8000/api/inventory/alerts/daily-report" -H "Authorization: Bearer YOUR_TOKEN"`

### Option 2: Linux/Mac Cron

```bash
# Open crontab
crontab -e

# Add this line for daily 9 AM alerts:
0 9 * * * curl -X POST "http://localhost:8000/api/inventory/alerts/daily-report" -H "Authorization: Bearer YOUR_TOKEN"
```

### Option 3: Python Script

Create `alert_scheduler.py`:

```python
from apscheduler.schedulers.blocking import BlockingScheduler
import requests

def send_daily_report():
    response = requests.post(
        "http://localhost:8000/api/inventory/alerts/daily-report",
        headers={"Authorization": "Bearer YOUR_TOKEN"}
    )
    print(f"Alert sent: {response.json()}")

scheduler = BlockingScheduler()
scheduler.add_job(send_daily_report, 'cron', hour=9)  # Daily at 9 AM

print("Scheduler started. Press Ctrl+C to exit.")
scheduler.start()
```

Run it:
```bash
pip install apscheduler
python alert_scheduler.py
```

---

## 📋 All Available Alerts

| Endpoint | Purpose | When to Use |
|----------|---------|-------------|
| `/alerts/test-telegram` | Test connection | Initial setup |
| `/alerts/low-stock` | Items below threshold | Every 6 hours |
| `/alerts/reorder` | Items needing order | Daily morning |
| `/alerts/out-of-stock` | Zero stock items | Immediately when detected |
| `/alerts/summary` | Statistics overview | Daily or weekly |
| `/alerts/daily-report` | Complete report | Every morning |
| `/alerts/custom` | Your own message | Anytime |

---

## 🎯 Common Use Cases

### 1. Morning Routine
```bash
# Send comprehensive report every morning
curl -X POST "http://localhost:8000/api/inventory/alerts/daily-report" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. Before Ordering
```bash
# Check what needs reordering
curl -X POST "http://localhost:8000/api/inventory/alerts/reorder" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Custom Announcement
```bash
# Notify team about something
curl -X POST "http://localhost:8000/api/inventory/alerts/custom" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "🎉 <b>New shipment arriving tomorrow!</b>"}'
```

---

## 🔧 Troubleshooting

### ❌ Problem: "Telegram not configured"
✅ **Solution:**
1. Check `.env` has all 3 variables
2. Make sure `TELEGRAM_ALERTS_ENABLED=true`
3. Restart your server: `Ctrl+C` then `uvicorn main:app --reload`

### ❌ Problem: "Chat not found"
✅ **Solution:**
1. Start a conversation with your bot first
2. Send any message
3. Get the correct Chat ID from getUpdates

### ❌ Problem: "Unauthorized"
✅ **Solution:**
1. Your bot token is wrong
2. Go back to @BotFather
3. Send `/token` to get your bot's token

### ❌ Problem: No message received
✅ **Solution:**
1. Check you're not blocking the bot
2. Verify the bot is active in @BotFather
3. Try the test endpoint first

---

## 🎨 Customize Your Messages

### Use HTML Formatting

```bash
curl -X POST "http://localhost:8000/api/inventory/alerts/custom" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "🔥 <b>URGENT</b>\n\n<i>Warehouse A is running low!</i>\n\n<code>Check inventory now</code>"
  }'
```

**Result:**
```
🔥 URGENT

Warehouse A is running low!

Check inventory now
```

### Add Emojis

Popular emojis for inventory:
- 🚨 Alert
- ⚠️ Warning
- 📦 Package/Stock
- 🔴 Urgent
- ✅ Success
- ❌ Out of stock
- 📍 Location
- 🔖 SKU/Tag
- 📊 Statistics

---

## 📞 Need Help?

1. **Test connection first:** 
   - `GET /api/inventory/alerts/test-telegram`
   
2. **Check logs:**
   - Look for `[TELEGRAM]` in your server output
   
3. **Verify settings:**
   ```python
   from app.core.config import settings
   print(settings.TELEGRAM_BOT_TOKEN)
   print(settings.TELEGRAM_CHAT_ID)
   print(settings.TELEGRAM_ALERTS_ENABLED)
   ```

4. **Manual test:**
   - Open: `https://api.telegram.org/botYOUR_TOKEN/sendMessage?chat_id=YOUR_CHAT_ID&text=Test`

---

## ✅ You're Done!

You now have:
- ✅ Telegram bot configured
- ✅ Low stock alerts working
- ✅ Multiple alert types available
- ✅ Rich formatted messages
- ✅ Ready for automation

**Next Steps:**
1. Set up daily automated alerts (cron or Task Scheduler)
2. Adjust `low_stock_threshold` for your products
3. Create a team group and add your bot
4. Customize alert schedules for your business

---

## 🌟 Pro Tips

1. **Create a dedicated alert channel:**
   - Create a private Telegram group
   - Add your bot to the group
   - Use the group's Chat ID (will be negative)
   - All team members get notifications

2. **Test with dummy data:**
   ```sql
   -- Create test product with low stock
   INSERT INTO inventory (product_id, stock_quantity, low_stock_threshold)
   VALUES (1, 5, 10);
   ```

3. **Don't spam:**
   - Use daily reports instead of checking every minute
   - Set reasonable thresholds
   - Use scheduled tasks, not manual triggers

4. **Monitor your bot:**
   - Check audit logs: `GET /api/audit-logs?resource_type=Inventory`
   - Review Telegram message history
   - Track alert patterns

---

## 📚 Full Documentation

For advanced features, see:
- `TELEGRAM_ALERTS_SETUP_GUIDE.md` - Complete guide
- `TELEGRAM_ALERTS_SUMMARY.md` - Technical details
- `INVENTORY_MANAGEMENT_GUIDE.md` - Inventory system guide

---

**Congratulations! Your inventory now sends Telegram alerts! 🎉**
