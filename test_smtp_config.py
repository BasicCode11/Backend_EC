"""Test script to check if SMTP environment variables are loaded"""
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

print("=" * 80)
print("SMTP Configuration Check")
print("=" * 80)

smtp_settings = {
    "SMTP_HOST": os.getenv("SMTP_HOST"),
    "SMTP_PORT": os.getenv("SMTP_PORT"),
    "SMTP_USER": os.getenv("SMTP_USER"),
    "SMTP_PASSWORD": os.getenv("SMTP_PASSWORD"),
    "SMTP_FROM_EMAIL": os.getenv("SMTP_FROM_EMAIL"),
    "SMTP_FROM_NAME": os.getenv("SMTP_FROM_NAME"),
}

for key, value in smtp_settings.items():
    if value:
        if key == "SMTP_PASSWORD":
            print(f"[OK] {key}: {'*' * len(value)} (length: {len(value)})")
        else:
            print(f"[OK] {key}: {value}")
    else:
        print(f"[MISSING] {key}: NOT SET")

print("=" * 80)

# Check if all required settings are present
if all([smtp_settings["SMTP_HOST"], smtp_settings["SMTP_USER"], smtp_settings["SMTP_PASSWORD"]]):
    print("[OK] All required SMTP settings are configured!")
    print("\nNow testing SMTP connection...")
    
    import smtplib
    try:
        with smtplib.SMTP(smtp_settings["SMTP_HOST"], int(smtp_settings["SMTP_PORT"])) as server:
            server.starttls()
            server.login(smtp_settings["SMTP_USER"], smtp_settings["SMTP_PASSWORD"])
            print("[OK] SMTP connection successful!")
            print("[OK] Email sending should work!")
    except Exception as e:
        print(f"[ERROR] SMTP connection failed: {e}")
        print("\nPossible issues:")
        print("1. Gmail requires 2-Step Verification + App Password")
        print("2. Check if 'Less secure app access' is enabled (if not using app password)")
        print("3. Verify your email and password are correct")
else:
    print("[ERROR] Some SMTP settings are missing!")
    print("\nPlease add them to your .env file:")
    print("SMTP_HOST=smtp.gmail.com")
    print("SMTP_PORT=587")
    print("SMTP_USER=your-email@gmail.com")
    print("SMTP_PASSWORD=your-app-password")

print("=" * 80)
