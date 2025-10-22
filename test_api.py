#!/usr/bin/env python3
"""
Test script to verify the API endpoints are working correctly.
Run this after starting the FastAPI server to test the authentication and user management.
"""

import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:8000/api"

def test_customer_registration():
    """Test customer registration"""
    print("🧪 Testing Customer Registration...")
    
    url = f"{BASE_URL}/register"
    data = {
        "email": "testcustomer@example.com",
        "password": "test123",
        "first_name": "Test",
        "last_name": "Customer",
        "phone": "+1234567899"
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print("✅ Customer registration successful")
            return response.json()
        else:
            print(f"❌ Registration failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return None

def test_admin_login():
    """Test admin login"""
    print("🧪 Testing Admin Login...")
    
    url = f"{BASE_URL}/login"
    data = {
        "email": "admin@example.com",
        "password": "admin123"
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print("✅ Admin login successful")
            return response.json()
        else:
            print(f"❌ Admin login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Admin login error: {e}")
        return None

def test_customer_login():
    """Test customer login"""
    print("🧪 Testing Customer Login...")
    
    url = f"{BASE_URL}/login"
    data = {
        "email": "customer1@example.com",
        "password": "customer123"
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print("✅ Customer login successful")
            return response.json()
        else:
            print(f"❌ Customer login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Customer login error: {e}")
        return None

def test_admin_user_management(token):
    """Test admin user management endpoints"""
    print("🧪 Testing Admin User Management...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test get users
    try:
        response = requests.get(f"{BASE_URL}/user", headers=headers)
        if response.status_code == 200:
            users = response.json()
            print(f"✅ Admin can list users: {len(users)} users found")
        else:
            print(f"❌ Admin user list failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Admin user list error: {e}")

def test_customer_restrictions(token):
    """Test that customers can't access admin endpoints"""
    print("🧪 Testing Customer Access Restrictions...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test get users (should fail for customer)
    try:
        response = requests.get(f"{BASE_URL}/user", headers=headers)
        if response.status_code == 403:
            print("✅ Customer correctly blocked from admin endpoints")
        else:
            print(f"⚠️ Customer access restriction not working: {response.status_code}")
    except Exception as e:
        print(f"❌ Customer restriction test error: {e}")

def main():
    """Run all tests"""
    print("🧪 API Testing Suite")
    print("=" * 50)
    
    # Test customer registration
    customer_data = test_customer_registration()
    
    # Test admin login
    admin_data = test_admin_login()
    if admin_data:
        admin_token = admin_data.get("access_token")
        if admin_token:
            test_admin_user_management(admin_token)
    
    # Test customer login
    customer_login_data = test_customer_login()
    if customer_login_data:
        customer_token = customer_login_data.get("access_token")
        if customer_token:
            test_customer_restrictions(customer_token)
    
    print("\n🎉 API testing completed!")
    print("=" * 50)

if __name__ == "__main__":
    main()
