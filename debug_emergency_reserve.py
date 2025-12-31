#!/usr/bin/env python3
"""
Debug script to investigate emergency reserve calculation
"""

import requests
import json

def debug_emergency_reserve():
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
    
    # Get categories to find "Reserva de Emergência" ID
    response = requests.get(f"{api_url}/categories", headers=headers)
    categories = response.json()
    
    reserve_category_id = None
    for cat in categories:
        if cat.get('name') == 'Reserva de Emergência':
            reserve_category_id = cat.get('id')
            print(f"Found 'Reserva de Emergência' category with ID: {reserve_category_id}")
            break
    
    # Get all transactions
    response = requests.get(f"{api_url}/transactions", headers=headers)
    all_transactions = response.json()
    
    print(f"\nAnalyzing {len(all_transactions)} transactions for emergency reserve calculation:")
    
    total_reserve = 0
    reserve_transactions = []
    
    for trans in all_transactions:
        # Check if it's marked as reserve deposit/withdrawal
        if trans.get('is_reserve_deposit'):
            total_reserve += trans['amount']
            reserve_transactions.append(f"+ R$ {trans['amount']} (reserve deposit): {trans.get('description', 'No desc')}")
        elif trans.get('is_reserve_withdrawal'):
            total_reserve -= trans['amount']
            reserve_transactions.append(f"- R$ {trans['amount']} (reserve withdrawal): {trans.get('description', 'No desc')}")
        # Check if it's categorized as "Reserva de Emergência"
        elif reserve_category_id and trans.get('category_id') == reserve_category_id:
            if trans.get('type') == 'receita':
                total_reserve += trans['amount']
                reserve_transactions.append(f"+ R$ {trans['amount']} (reserve category, receita): {trans.get('description', 'No desc')}")
            else:
                total_reserve -= trans['amount']
                reserve_transactions.append(f"- R$ {trans['amount']} (reserve category, despesa): {trans.get('description', 'No desc')}")
    
    print("\nTransactions contributing to emergency reserve:")
    for rt in reserve_transactions:
        print(f"  {rt}")
    
    print(f"\nCalculated total: R$ {total_reserve}")
    
    # Get API result
    response = requests.get(f"{api_url}/dashboard/emergency-reserve", headers=headers)
    api_result = response.json()
    print(f"API result: R$ {api_result.get('total', 0)}")

if __name__ == "__main__":
    debug_emergency_reserve()