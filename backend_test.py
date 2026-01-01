import requests
import sys
import json
from datetime import datetime
import uuid

class FinancialAppTester:
    def __init__(self, base_url="https://moneymaster-32.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        # Test credentials for existing user
        self.test_email = "super@finamily.com"
        self.test_password = "Admin@2025"

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    # Remove Content-Type for file uploads
                    headers.pop('Content-Type', None)
                    response = requests.post(url, data=data, files=files, headers=headers)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                details += f", Expected: {expected_status}"
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Response: {response.text[:100]}"

            self.log_test(name, success, details)
            
            if success:
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                return False, {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_auth_register(self):
        """Test user registration"""
        test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        test_data = {
            "email": test_email,
            "password": "TestPass123!",
            "name": "Test User"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=test_data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_data = response['user']
            return True
        return False

    def test_auth_login_existing_user(self):
        """Test login with existing test user"""
        login_data = {
            "email": self.test_email,
            "password": self.test_password
        }
        
        success, response = self.run_test(
            "Login with Test User",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_data = response['user']
            return True
        return False

    def test_profile_endpoints(self):
        """Test profile-related endpoints"""
        # Test GET /api/profile
        success, response = self.run_test(
            "Get Profile Data",
            "GET",
            "profile",
            200
        )
        
        if not success:
            return False
            
        # Verify profile data structure
        profile_data = response
        expected_fields = ['id', 'email', 'name', 'is_admin']
        missing_fields = [field for field in expected_fields if field not in profile_data]
        
        if missing_fields:
            self.log_test("Profile Data Structure", False, f"Missing fields: {missing_fields}")
            return False
        else:
            self.log_test("Profile Data Structure", True, "All required fields present")
        
        # Test PUT /api/profile - Update name
        original_name = profile_data.get('name', '')
        update_data = {
            "name": "Updated Test Name"
        }
        
        success, response = self.run_test(
            "Update Profile Name",
            "PUT",
            "profile",
            200,
            data=update_data
        )
        
        if not success:
            return False
            
        # Verify name was updated
        if response.get('name') == "Updated Test Name":
            self.log_test("Profile Name Update Verification", True, "Name updated correctly")
        else:
            self.log_test("Profile Name Update Verification", False, f"Expected 'Updated Test Name', got '{response.get('name')}'")
            return False
        
        # Restore original name
        restore_data = {"name": original_name}
        success, response = self.run_test(
            "Restore Original Profile Name",
            "PUT",
            "profile",
            200,
            data=restore_data
        )
        
        return success

    def test_change_password_endpoint(self):
        """Test password change endpoint with incorrect current password"""
        # Test with INCORRECT current password (should fail)
        password_data = {
            "current_password": "WrongPassword123!",
            "new_password": "NewPassword123!"
        }
        
        success, response = self.run_test(
            "Change Password with Wrong Current Password",
            "POST",
            "profile/change-password",
            400,  # Should fail with 400
            data=password_data
        )
        
        # This test passes if it correctly returns 400 (bad request)
        return success

    def test_delete_all_transactions_endpoint(self):
        """Test that delete all transactions endpoint exists (without executing)"""
        # We'll test with a HEAD request or check if endpoint exists
        # by making a request without proper auth to see if endpoint is recognized
        
        # Remove token temporarily to test endpoint existence
        original_token = self.token
        self.token = "invalid_token"
        
        success, response = self.run_test(
            "Delete All Transactions Endpoint Exists",
            "DELETE",
            "transactions/delete-all",
            401,  # Should return 401 for invalid token, proving endpoint exists
        )
        
        # Restore token
        self.token = original_token
        
        # If we get 401, it means the endpoint exists but auth failed (which is expected)
        return success

    def test_transactions_with_category_filter(self):
        """Test transactions endpoint with category filtering"""
        # First get categories to find "Reserva de Emergência"
        success, categories_response = self.run_test(
            "Get Categories for Filter Test",
            "GET",
            "categories",
            200
        )
        
        if not success:
            return False
            
        # Find "Reserva de Emergência" category
        emergency_category = None
        for category in categories_response:
            if category.get('name') == 'Reserva de Emergência':
                emergency_category = category
                break
        
        if not emergency_category:
            self.log_test("Find Emergency Reserve Category", False, "Reserva de Emergência category not found")
            return False
        else:
            self.log_test("Find Emergency Reserve Category", True, f"Found category with ID: {emergency_category['id']}")
        
        # Get all transactions
        success, all_transactions = self.run_test(
            "Get All Transactions",
            "GET",
            "transactions",
            200
        )
        
        if not success:
            return False
            
        # Count transactions with "Reserva de Emergência" category
        emergency_transactions = [
            t for t in all_transactions 
            if t.get('category_id') == emergency_category['id']
        ]
        
        expected_count = 2  # According to review request
        actual_count = len(emergency_transactions)
        
        if actual_count == expected_count:
            self.log_test("Emergency Reserve Transactions Count", True, f"Found {actual_count} transactions as expected")
            return True
        else:
            self.log_test("Emergency Reserve Transactions Count", False, f"Expected {expected_count}, found {actual_count}")
            return False

    def test_family_crud(self):
        """Test family member CRUD operations"""
        # Create member
        member_data = {"name": "Test Member", "profile": "Test Profile"}
        success, response = self.run_test(
            "Create Family Member",
            "POST",
            "family",
            200,
            data=member_data
        )
        
        if not success:
            return False
            
        member_id = response.get('id')
        
        # Get members
        success, response = self.run_test(
            "Get Family Members",
            "GET",
            "family",
            200
        )
        
        if not success:
            return False
            
        # Update member
        update_data = {"name": "Updated Member", "profile": "Updated Profile"}
        success, response = self.run_test(
            "Update Family Member",
            "PUT",
            f"family/{member_id}",
            200,
            data=update_data
        )
        
        if not success:
            return False
            
        # Delete member
        success, response = self.run_test(
            "Delete Family Member",
            "DELETE",
            f"family/{member_id}",
            200
        )
        
        return success

    def test_banks_crud(self):
        """Test bank CRUD operations"""
        # Create bank
        bank_data = {"name": "Test Bank", "active": True}
        success, response = self.run_test(
            "Create Bank",
            "POST",
            "banks",
            200,
            data=bank_data
        )
        
        if not success:
            return False
            
        bank_id = response.get('id')
        
        # Get banks
        success, response = self.run_test(
            "Get Banks",
            "GET",
            "banks",
            200
        )
        
        if not success:
            return False
            
        # Update bank
        update_data = {"name": "Updated Bank", "active": False}
        success, response = self.run_test(
            "Update Bank",
            "PUT",
            f"banks/{bank_id}",
            200,
            data=update_data
        )
        
        if not success:
            return False
            
        # Delete bank
        success, response = self.run_test(
            "Delete Bank",
            "DELETE",
            f"banks/{bank_id}",
            200
        )
        
        return success

    def test_categories_crud(self):
        """Test category CRUD operations"""
        # Create category
        category_data = {"name": "Test Category", "type": "despesa"}
        success, response = self.run_test(
            "Create Category",
            "POST",
            "categories",
            200,
            data=category_data
        )
        
        if not success:
            return False
            
        category_id = response.get('id')
        
        # Get categories
        success, response = self.run_test(
            "Get Categories",
            "GET",
            "categories",
            200
        )
        
        if not success:
            return False
            
        # Update category
        update_data = {"name": "Updated Category", "type": "receita"}
        success, response = self.run_test(
            "Update Category",
            "PUT",
            f"categories/{category_id}",
            200,
            data=update_data
        )
        
        if not success:
            return False
            
        # Delete category
        success, response = self.run_test(
            "Delete Category",
            "DELETE",
            f"categories/{category_id}",
            200
        )
        
        return success

    def test_dashboard_endpoints(self):
        """Test dashboard data endpoints"""
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Test dashboard summary
        success, response = self.run_test(
            "Dashboard Summary",
            "GET",
            f"dashboard/summary?month={current_month}&year={current_year}",
            200
        )
        
        if not success:
            return False
            
        # Test category chart
        success, response = self.run_test(
            "Category Chart Data",
            "GET",
            f"dashboard/category-chart?month={current_month}&year={current_year}",
            200
        )
        
        if not success:
            return False
            
        # Test monthly comparison
        success, response = self.run_test(
            "Monthly Comparison Data",
            "GET",
            f"dashboard/monthly-comparison?year={current_year}",
            200
        )
        
        return success

    def test_transactions_endpoints(self):
        """Test transaction endpoints"""
        # Get transactions
        success, response = self.run_test(
            "Get Transactions",
            "GET",
            "transactions",
            200
        )
        
        return success

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Financial App Backend Tests")
        print("=" * 50)
        
        # Test authentication
        if not self.test_auth_register():
            print("❌ Registration failed, stopping tests")
            return False
            
        if not self.test_auth_login():
            print("❌ Login failed, stopping tests")
            return False
            
        # Test CRUD operations
        self.test_family_crud()
        self.test_banks_crud()
        self.test_categories_crud()
        
        # Test dashboard endpoints
        self.test_dashboard_endpoints()
        
        # Test transactions
        self.test_transactions_endpoints()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Tests Summary: {self.tests_passed}/{self.tests_run} passed")
        print(f"✅ Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = FinancialAppTester()
    success = tester.run_all_tests()
    
    # Save detailed results
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_tests": tester.tests_run,
            "passed_tests": tester.tests_passed,
            "success_rate": (tester.tests_passed/tester.tests_run)*100 if tester.tests_run > 0 else 0,
            "results": tester.test_results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())