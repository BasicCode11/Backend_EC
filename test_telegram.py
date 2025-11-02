"""
Quick test script for Telegram bot connection
"""
import httpx
import sys
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Your bot credentials
BOT_TOKEN = "8597164603:AAEFa_HjG2L8UmRmQDeVh_8jENnd_GsvOYs"
CHAT_ID = "-1003143140650"

def test_telegram():
    """Send a test message to verify bot is working"""
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    message = """
🤖 <b>Telegram Bot Test</b>

✅ Your bot is configured correctly!

<b>Bot Details:</b>
• Bot: @vortexdevstore_bot
• Chat ID: -1003143140650 (Group)
• Status: Active

<b>What's Next?</b>
🔹 Start your FastAPI server
🔹 Go to http://localhost:8000/docs
🔹 Try the alert endpoints

<i>Test completed successfully!</i>
    """
    
    payload = {
        "chat_id": CHAT_ID,
        "text": message.strip(),
        "parse_mode": "HTML"
    }
    
    print("=" * 60)
    print("🚀 Testing Telegram Bot Connection...")
    print("=" * 60)
    print(f"Bot Token: {BOT_TOKEN[:20]}...")
    print(f"Chat ID: {CHAT_ID}")
    print(f"Sending message...")
    print("=" * 60)
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
        
        if result.get("ok"):
            print("✅ SUCCESS! Message sent to Telegram!")
            print(f"Message ID: {result['result']['message_id']}")
            print("\n📱 Check your Telegram group for the message!")
            print("=" * 60)
            return True
        else:
            print("❌ FAILED!")
            print(f"Error: {result}")
            return False
            
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error: {e.response.status_code}")
        print(f"Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_telegram()
