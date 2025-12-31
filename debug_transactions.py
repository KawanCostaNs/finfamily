#!/usr/bin/env python3
"""
Debug script to investigate the transactions filter issue
"""

import requests
import json
from datetime import datetime

def debug_transactions():
    base_url = "https://moneymaster-32.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Login first
    login_data = {
        "email": "super@finamily.com",
        "password": "Admin@2025"
    }
    
    response = requests.post(f"{api_url}/auth/login", json=login_data)
    if response.status_code != 200:
        print("Login failed")
        return
    
    token = response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get all transactions
    response = requests.get(f"{api_url}/transactions", headers=headers)
    all_transactions = response.json()
    
    print(f"Total transactions: {len(all_transactions)}")
    print("\nAll transactions:")
    for i, trans in enumerate(all_transactions, 1):
        date_str = trans.get('date', 'No date')
        if isinstance(date_str, str) and 'T' in date_str:
            try:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                date_str = dt.strftime('%Y-%m-%d')
            except:
                pass
        print(f"{i}. {date_str} - {trans.get('description', 'No desc')} - R$ {trans.get('amount', 0)} ({trans.get('type', 'No type')})")
    
    # Get January 2025 transactions
    response = requests.get(f"{api_url}/transactions?month=1&year=2025", headers=headers)
    january_transactions = response.json()
    
    print(f"\nJanuary 2025 transactions: {len(january_transactions)}")
    for i, trans in enumerate(january_transactions, 1):
        date_str = trans.get('date', 'No date')
        if isinstance(date_str, str) and 'T' in date_str:
            try:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                date_str = dt.strftime('%Y-%m-%d')
            except:
                pass
        print(f"{i}. {date_str} - {trans.get('description', 'No desc')} - R$ {trans.get('amount', 0)} ({trans.get('type', 'No type')})")

if __name__ == "__main__":
    debug_transactions()