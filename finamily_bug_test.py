#!/usr/bin/env python3
"""
FinFamily Bug Fix Testing Script
Tests the 3 specific bugs that were reportedly fixed:
1. Emergency Reserve calculation
2. Revenue vs Expense chart data
3. Month/Year filters on transactions
"""

import requests
import json
from datetime import datetime

class FinFamilyBugTester:
    def __init__(self):
        self.base_url = "https://finamily-app.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.token = None
        self.test_results = []
        
    def log_result(self, test_name, success, details="", expected=None, actual=None):
        """Log test result with details"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if details:
            print(f"    Details: {details}")
        if expected is not None and actual is not None:
            print(f"    Expected: {expected}")
            print(f"    Actual: {actual}")
        print()
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "expected": expected,
            "actual": actual
        })
        
    def make_request(self, method, endpoint, data=None, params=None):
        """Make API request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
            
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
                
            return response
        except Exception as e:
            print(f"Request failed: {e}")
            return None
    
    def test_login(self):
        """Test login with provided credentials"""
        print("🔐 Testing Login...")
        
        login_data = {
            "email": "super@finamily.com",
            "password": "Admin@2025"
        }
        
        response = self.make_request('POST', 'auth/login', data=login_data)
        
        if not response:
            self.log_result("Login API", False, "Request failed")
            return False
            
        if response.status_code == 200:
            try:
                data = response.json()
                if 'access_token' in data:
                    self.token = data['access_token']
                    self.log_result("Login API", True, f"Successfully logged in as {data.get('user', {}).get('email', 'unknown')}")
                    return True
                else:
                    self.log_result("Login API", False, "No access token in response", None, data)
                    return False
            except Exception as e:
                self.log_result("Login API", False, f"Failed to parse response: {e}")
                return False
        else:
            try:
                error_data = response.json()
                self.log_result("Login API", False, f"HTTP {response.status_code}: {error_data.get('detail', 'Unknown error')}")
            except:
                self.log_result("Login API", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def test_emergency_reserve(self):
        """Test Bug #1: Emergency Reserve calculation should return R$ 2.000,00"""
        print("💰 Testing Emergency Reserve Calculation...")
        
        response = self.make_request('GET', 'dashboard/emergency-reserve')
        
        if not response:
            self.log_result("Emergency Reserve API", False, "Request failed")
            return False
            
        if response.status_code == 200:
            try:
                data = response.json()
                expected_total = 2000.0
                actual_total = data.get('total', 0)
                
                success = actual_total == expected_total
                self.log_result(
                    "Emergency Reserve API", 
                    success, 
                    f"Reserve total calculation",
                    f"R$ {expected_total}",
                    f"R$ {actual_total}"
                )
                return success
            except Exception as e:
                self.log_result("Emergency Reserve API", False, f"Failed to parse response: {e}")
                return False
        else:
            try:
                error_data = response.json()
                self.log_result("Emergency Reserve API", False, f"HTTP {response.status_code}: {error_data.get('detail', 'Unknown error')}")
            except:
                self.log_result("Emergency Reserve API", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def test_dashboard_summary(self):
        """Test dashboard summary for January 2025"""
        print("📊 Testing Dashboard Summary for January 2025...")
        
        params = {'month': 1, 'year': 2025}
        response = self.make_request('GET', 'dashboard/summary', params=params)
        
        if not response:
            self.log_result("Dashboard Summary API", False, "Request failed")
            return False
            
        if response.status_code == 200:
            try:
                data = response.json()
                required_fields = ['previous_balance', 'month_income', 'month_expenses', 'final_balance']
                
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    self.log_result(
                        "Dashboard Summary API", 
                        False, 
                        f"Missing fields: {missing_fields}",
                        required_fields,
                        list(data.keys())
                    )
                    return False
                
                # Check if we have reasonable data for January 2025
                month_income = data.get('month_income', 0)
                month_expenses = data.get('month_expenses', 0)
                
                self.log_result(
                    "Dashboard Summary API", 
                    True, 
                    f"January 2025 - Income: R$ {month_income}, Expenses: R$ {month_expenses}"
                )
                return True
                
            except Exception as e:
                self.log_result("Dashboard Summary API", False, f"Failed to parse response: {e}")
                return False
        else:
            try:
                error_data = response.json()
                self.log_result("Dashboard Summary API", False, f"HTTP {response.status_code}: {error_data.get('detail', 'Unknown error')}")
            except:
                self.log_result("Dashboard Summary API", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def test_monthly_comparison(self):
        """Test Bug #2: Monthly comparison chart should separate receita (green) vs despesa (red)"""
        print("📈 Testing Monthly Comparison Chart Data for 2025...")
        
        params = {'year': 2025}
        response = self.make_request('GET', 'dashboard/monthly-comparison', params=params)
        
        if not response:
            self.log_result("Monthly Comparison API", False, "Request failed")
            return False
            
        if response.status_code == 200:
            try:
                data = response.json()
                
                if not isinstance(data, list):
                    self.log_result("Monthly Comparison API", False, "Response should be a list", "list", type(data).__name__)
                    return False
                
                # Check if we have 12 months
                if len(data) != 12:
                    self.log_result("Monthly Comparison API", False, f"Should have 12 months", 12, len(data))
                    return False
                
                # Find January data
                january_data = None
                for month_data in data:
                    if month_data.get('month') == 'Jan':
                        january_data = month_data
                        break
                
                if not january_data:
                    self.log_result("Monthly Comparison API", False, "January data not found")
                    return False
                
                # Check that income and expenses are separate fields
                income = january_data.get('income', 0)
                expenses = january_data.get('expenses', 0)
                
                # Based on the review request, January should have ~R$ 6.000 receita and ~R$ 535 despesa
                expected_income_range = (5000, 7000)  # Allow some variance
                expected_expenses_range = (400, 700)   # Allow some variance
                
                income_ok = expected_income_range[0] <= income <= expected_income_range[1]
                expenses_ok = expected_expenses_range[0] <= expenses <= expected_expenses_range[1]
                
                if income_ok and expenses_ok:
                    self.log_result(
                        "Monthly Comparison API", 
                        True, 
                        f"January 2025 - Income: R$ {income}, Expenses: R$ {expenses} (within expected ranges)"
                    )
                    return True
                else:
                    self.log_result(
                        "Monthly Comparison API", 
                        False, 
                        f"January 2025 values outside expected ranges",
                        f"Income: {expected_income_range}, Expenses: {expected_expenses_range}",
                        f"Income: {income}, Expenses: {expenses}"
                    )
                    return False
                    
            except Exception as e:
                self.log_result("Monthly Comparison API", False, f"Failed to parse response: {e}")
                return False
        else:
            try:
                error_data = response.json()
                self.log_result("Monthly Comparison API", False, f"HTTP {response.status_code}: {error_data.get('detail', 'Unknown error')}")
            except:
                self.log_result("Monthly Comparison API", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def test_transactions_filters(self):
        """Test Bug #3: Transactions should support month/year filtering"""
        print("📝 Testing Transactions with Month/Year Filters...")
        
        # Test 1: Get all transactions
        response = self.make_request('GET', 'transactions')
        
        if not response or response.status_code != 200:
            self.log_result("Transactions API (All)", False, "Failed to get all transactions")
            return False
        
        try:
            all_transactions = response.json()
            total_count = len(all_transactions)
            
            self.log_result("Transactions API (All)", True, f"Retrieved {total_count} total transactions")
            
            # Test 2: Filter by January 2025 (should show only 4 transactions according to review request)
            params = {'month': 1, 'year': 2025}
            response = self.make_request('GET', 'transactions', params=params)
            
            if not response or response.status_code != 200:
                self.log_result("Transactions API (January Filter)", False, "Failed to get January transactions")
                return False
            
            january_transactions = response.json()
            january_count = len(january_transactions)
            
            # According to review request, January should have 4 transactions
            expected_january_count = 4
            
            if january_count == expected_january_count:
                self.log_result(
                    "Transactions API (January Filter)", 
                    True, 
                    f"January 2025 filter returned {january_count} transactions as expected"
                )
            else:
                self.log_result(
                    "Transactions API (January Filter)", 
                    False, 
                    f"January 2025 filter count mismatch",
                    expected_january_count,
                    january_count
                )
                return False
            
            # Test 3: Verify filtering actually works (filtered count should be less than total)
            if january_count < total_count:
                self.log_result("Transactions Filtering Logic", True, f"Filtering works: {january_count} < {total_count}")
                return True
            else:
                self.log_result("Transactions Filtering Logic", False, "Filtering doesn't seem to work - same count as total")
                return False
                
        except Exception as e:
            self.log_result("Transactions API", False, f"Failed to parse response: {e}")
            return False
    
    def test_categories(self):
        """Test categories endpoint to verify 'Reserva de Emergência' category exists"""
        print("🏷️ Testing Categories...")
        
        response = self.make_request('GET', 'categories')
        
        if not response:
            self.log_result("Categories API", False, "Request failed")
            return False
            
        if response.status_code == 200:
            try:
                categories = response.json()
                
                # Look for "Reserva de Emergência" category
                reserve_category = None
                for cat in categories:
                    if cat.get('name') == 'Reserva de Emergência':
                        reserve_category = cat
                        break
                
                if reserve_category:
                    self.log_result(
                        "Categories API", 
                        True, 
                        f"Found 'Reserva de Emergência' category with type: {reserve_category.get('type', 'unknown')}"
                    )
                    return True
                else:
                    category_names = [cat.get('name', 'unnamed') for cat in categories]
                    self.log_result(
                        "Categories API", 
                        False, 
                        "'Reserva de Emergência' category not found",
                        "'Reserva de Emergência' in categories",
                        f"Available categories: {category_names}"
                    )
                    return False
                    
            except Exception as e:
                self.log_result("Categories API", False, f"Failed to parse response: {e}")
                return False
        else:
            try:
                error_data = response.json()
                self.log_result("Categories API", False, f"HTTP {response.status_code}: {error_data.get('detail', 'Unknown error')}")
            except:
                self.log_result("Categories API", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def run_all_tests(self):
        """Run all bug fix tests"""
        print("🚀 FinFamily Bug Fix Testing")
        print("=" * 60)
        print("Testing 3 specific bugs that were reportedly fixed:")
        print("1. Emergency Reserve calculation")
        print("2. Revenue vs Expense chart separation")
        print("3. Month/Year filters on transactions")
        print("=" * 60)
        print()
        
        # Step 1: Login
        if not self.test_login():
            print("❌ Cannot proceed without authentication")
            return False
        
        # Step 2: Test each bug fix
        results = []
        results.append(self.test_emergency_reserve())
        results.append(self.test_dashboard_summary())
        results.append(self.test_monthly_comparison())
        results.append(self.test_transactions_filters())
        results.append(self.test_categories())
        
        # Summary
        passed = sum(results)
        total = len(results)
        
        print("=" * 60)
        print(f"📊 FINAL RESULTS: {passed}/{total} tests passed")
        print(f"✅ Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 All bug fixes are working correctly!")
        else:
            print("⚠️  Some issues found - see details above")
        
        return passed == total

def main():
    """Main test execution"""
    tester = FinFamilyBugTester()
    success = tester.run_all_tests()
    
    # Save results to file
    timestamp = datetime.now().isoformat()
    results_data = {
        "timestamp": timestamp,
        "test_type": "FinFamily Bug Fix Testing",
        "total_tests": len(tester.test_results),
        "passed_tests": sum(1 for r in tester.test_results if r['success']),
        "success_rate": (sum(1 for r in tester.test_results if r['success']) / len(tester.test_results)) * 100 if tester.test_results else 0,
        "results": tester.test_results
    }
    
    with open('/app/finamily_bug_test_results.json', 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: /app/finamily_bug_test_results.json")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())