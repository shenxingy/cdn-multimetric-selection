#!/usr/bin/env python3
"""
Quick script to check RIPE Atlas credit balance
Run this before launching measurements to verify credits are available
"""

import os
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

PRIMARY_KEY = os.getenv('RIPE_ATLAS_PRIMARY_KEY')

if not PRIMARY_KEY:
    print("❌ Error: RIPE_ATLAS_PRIMARY_KEY not found in .env file")
    exit(1)

print("=" * 60)
print("RIPE Atlas Credit Check")
print("=" * 60)
print(f"API Key: {PRIMARY_KEY[:10]}...{PRIMARY_KEY[-4:]}")
print()

# Check credits via API
url = "https://atlas.ripe.net/api/v2/credits/"
headers = {
    "Authorization": f"Key {PRIMARY_KEY}",
    "Content-Type": "application/json"
}

try:
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        
        # Extract credit information
        current_balance = data.get('current_balance', 0)
        income_total = data.get('income_total', 0)
        expense_total = data.get('expense_total', 0)
        
        print(f"✅ Credit Balance: {current_balance:,} credits")
        print(f"   Total Income: {income_total:,} credits")
        print(f"   Total Expense: {expense_total:,} credits")
        print()
        
        if current_balance >= 1000:
            print("✅ EXCELLENT! You have plenty of credits for measurements")
            print(f"   You can run ~{current_balance // 15} minimal test measurements")
            print(f"   Or ~{current_balance // 225} full 1-hour measurements with 5 probes")
        elif current_balance >= 100:
            print("✅ GOOD! You have enough credits for several measurements")
            print(f"   You can run ~{current_balance // 15} minimal test measurements")
        elif current_balance >= 15:
            print("⚠️  LIMITED: You have enough for a few test measurements")
            print(f"   You can run ~{current_balance // 15} minimal test measurements")
        else:
            print("❌ INSUFFICIENT: You need more credits")
            print("   Minimum needed: 15 credits for a small test")
            print("   Request credits at: https://atlas.ripe.net/get-involved/benefits/")
        
        print()
        print("Measurement Cost Estimates:")
        print("  • 1-hour test (5 probes, 12 measurements): ~225 credits")
        print("  • 10-minute test (2 probes, 2 measurements): ~15 credits")
        print("  • 24-hour campaign (50 probes, 7 targets): ~50,400 credits")
        
    elif response.status_code == 403:
        print("❌ Error: API key doesn't have permission to check credits")
        print("   The key may not have the correct permissions")
    else:
        print(f"❌ Error: HTTP {response.status_code}")
        print(f"   Response: {response.text}")

except Exception as e:
    print(f"❌ Error checking credits: {e}")
    print()
    print("💡 Tip: You can also check credits at https://atlas.ripe.net/")

print("=" * 60)
