#!/usr/bin/env python3
"""
Setup test data for FinFamily backend testing
Creates sample transactions, family members, banks, etc. for admin@finamily.com
"""
import requests
import json
from datetime import datetime, timedelta
import uuid

class TestDataSetup:
    def __init__(self):
        self.base_url = "https://finamily-app.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.token = None
        self.user_data = None
        self.email = "admin@finamily.com"
        self.password = "Admin@2025"
        
    def login(self):
        """Login and get auth token"""
        login_data = {
            "email": self.email,
            "password": self.password
        }
        
        response = requests.post(f"{self.api_url}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            self.token = data['access_token']
            self.user_data = data['user']
            print(f"✅ Logged in as: {self.user_data['name']} ({self.user_data['email']})")
            return True
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
    
    def make_request(self, method, endpoint, data=None):
        """Make authenticated API request"""
        url = f"{self.api_url}/{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers)
        elif method == 'PUT':
            response = requests.put(url, json=data, headers=headers)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        
        return response
    
    def create_family_member(self):
        """Create a family member"""
        member_data = {
            "name": "João Silva",
            "profile": "Pai de família"
        }
        
        response = self.make_request('POST', 'family', member_data)
        if response.status_code == 200:
            member = response.json()
            print(f"✅ Created family member: {member['name']}")
            return member
        else:
            print(f"❌ Failed to create family member: {response.status_code}")
            return None
    
    def create_bank(self):
        """Create a bank"""
        bank_data = {
            "name": "Nubank",
            "active": True
        }
        
        response = self.make_request('POST', 'banks', bank_data)
        if response.status_code == 200:
            bank = response.json()
            print(f"✅ Created bank: {bank['name']}")
            return bank
        else:
            print(f"❌ Failed to create bank: {response.status_code}")
            return None
    
    def get_emergency_category(self):
        """Get the emergency reserve category"""
        response = self.make_request('GET', 'categories')
        if response.status_code == 200:
            categories = response.json()
            for cat in categories:
                if cat['name'] == 'Reserva de Emergência':
                    print(f"✅ Found emergency category: {cat['name']}")
                    return cat
            print("❌ Emergency reserve category not found")
            return None
        else:
            print(f"❌ Failed to get categories: {response.status_code}")
            return None
    
    def create_transactions_via_import(self, member_id, bank_id, emergency_category_id):
        """Create transactions via CSV import"""
        # Create CSV content with emergency reserve transactions
        csv_content = f"""Data,Descrição,Valor
2025-01-01,Salário Janeiro,5000.00
2025-01-02,Depósito Reserva,1000.00
2025-01-03,Freelance,2000.00
2025-01-05,Supermercado,-150.00
2025-01-10,Depósito Reserva,1000.00
2025-01-15,Transporte,-85.00
2025-01-20,Alimentação,-200.00
2025-01-25,Lazer,-100.00"""
        
        # Import transactions
        files = {'file': ('transactions.csv', csv_content, 'text/csv')}
        data = {
            'member_id': member_id,
            'bank_id': bank_id
        }
        
        url = f"{self.api_url}/transactions/import"
        headers = {'Authorization': f'Bearer {self.token}'}
        
        response = requests.post(url, data=data, files=files, headers=headers)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Imported {result['count']} transactions")
            return True
        else:
            print(f"❌ Failed to import transactions: {response.status_code} - {response.text}")
            return False
    
    def categorize_emergency_transactions(self, emergency_category_id):
        """Categorize the emergency reserve transactions"""
        # Get all transactions
        response = self.make_request('GET', 'transactions')
        if response.status_code != 200:
            print(f"❌ Failed to get transactions: {response.status_code}")
            return False
        
        transactions = response.json()
        emergency_transactions = []
        
        # Find transactions with "Depósito Reserva" in description
        for trans in transactions:
            if 'Depósito Reserva' in trans['description']:
                emergency_transactions.append(trans['id'])
        
        if not emergency_transactions:
            print("❌ No emergency reserve transactions found")
            return False
        
        # Bulk categorize them
        bulk_data = {
            "transaction_ids": emergency_transactions,
            "category_id": emergency_category_id
        }
        
        response = self.make_request('POST', 'transactions/bulk-categorize', bulk_data)
        if response.status_code == 200:
            print(f"✅ Categorized {len(emergency_transactions)} emergency reserve transactions")
            return True
        else:
            print(f"❌ Failed to categorize transactions: {response.status_code}")
            return False
    
    def create_challenge(self):
        """Create a family challenge"""
        challenge_data = {
            "name": "Economizar na Energia",
            "description": "Reduzir conta de luz em 20%",
            "target_amount": 200.0,
            "reward": "Jantar especial em família"
        }
        
        response = self.make_request('POST', 'gamification/challenges', challenge_data)
        if response.status_code == 200:
            challenge = response.json()
            print(f"✅ Created challenge: {challenge['name']}")
            return challenge
        else:
            print(f"❌ Failed to create challenge: {response.status_code}")
            return None
    
    def setup_all_data(self):
        """Setup all test data"""
        print("🚀 Setting up test data for FinFamily backend...")
        print("=" * 50)
        
        # Login
        if not self.login():
            return False
        
        # Create family member
        member = self.create_family_member()
        if not member:
            return False
        
        # Create bank
        bank = self.create_bank()
        if not bank:
            return False
        
        # Get emergency category
        emergency_category = self.get_emergency_category()
        if not emergency_category:
            return False
        
        # Import transactions
        if not self.create_transactions_via_import(member['id'], bank['id'], emergency_category['id']):
            return False
        
        # Categorize emergency transactions
        if not self.categorize_emergency_transactions(emergency_category['id']):
            return False
        
        # Create challenge
        challenge = self.create_challenge()
        if not challenge:
            return False
        
        # Check badges (this will unlock some badges based on the data)
        response = self.make_request('POST', 'gamification/check-badges')
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Checked badges: {result['count']} unlocked")
        
        print("=" * 50)
        print("✅ Test data setup completed successfully!")
        print("\nCreated:")
        print(f"- Family member: {member['name']}")
        print(f"- Bank: {bank['name']}")
        print(f"- 8 transactions (including 2 emergency reserve deposits)")
        print(f"- Challenge: {challenge['name']}")
        print("- Emergency reserve should now show R$ 2.000,00")
        
        return True

if __name__ == "__main__":
    setup = TestDataSetup()
    success = setup.setup_all_data()
    exit(0 if success else 1)