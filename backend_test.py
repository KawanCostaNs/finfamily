import requests
import sys
import json
from datetime import datetime
import uuid

class FinancialAppTester:
    def __init__(self, base_url="https://finamily-app.preview.emergentagent.com"):
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

    def test_gamification_health_score(self):
        """Test Health Score API"""
        success, response = self.run_test(
            "Get Health Score",
            "GET",
            "gamification/health-score",
            200
        )
        
        if not success:
            return False
            
        # Verify health score structure
        expected_fields = ['total_score', 'reserve_score', 'expense_ratio_score', 'consistency_score', 'goals_score', 'level', 'tips']
        missing_fields = [field for field in expected_fields if field not in response]
        
        if missing_fields:
            self.log_test("Health Score Structure", False, f"Missing fields: {missing_fields}")
            return False
        else:
            self.log_test("Health Score Structure", True, "All required fields present")
        
        # Verify score ranges
        total_score = response.get('total_score', -1)
        if 0 <= total_score <= 100:
            self.log_test("Health Score Range", True, f"Total score: {total_score}")
        else:
            self.log_test("Health Score Range", False, f"Total score {total_score} not in range 0-100")
            return False
        
        # Verify level is valid
        valid_levels = ["Crítico", "Atenção", "Bom", "Excelente"]
        level = response.get('level', '')
        if level in valid_levels:
            self.log_test("Health Score Level", True, f"Level: {level}")
        else:
            self.log_test("Health Score Level", False, f"Invalid level: {level}")
            return False
        
        # Verify tips is a list
        tips = response.get('tips', [])
        if isinstance(tips, list):
            self.log_test("Health Score Tips", True, f"Tips count: {len(tips)}")
        else:
            self.log_test("Health Score Tips", False, "Tips is not a list")
            return False
        
        return True

    def test_gamification_badges(self):
        """Test Badges API"""
        success, response = self.run_test(
            "Get Badges",
            "GET",
            "gamification/badges",
            200
        )
        
        if not success:
            return False
            
        # Verify badges structure
        if not isinstance(response, list):
            self.log_test("Badges Structure", False, "Response is not a list")
            return False
        
        if len(response) != 8:
            self.log_test("Badges Count", False, f"Expected 8 badges, got {len(response)}")
            return False
        else:
            self.log_test("Badges Count", True, "8 badges returned")
        
        # Check each badge structure
        expected_badge_fields = ['name', 'description', 'icon', 'criteria', 'unlocked', 'unlocked_at']
        for i, badge in enumerate(response):
            missing_fields = [field for field in expected_badge_fields if field not in badge]
            if missing_fields:
                self.log_test(f"Badge {i+1} Structure", False, f"Missing fields: {missing_fields}")
                return False
        
        self.log_test("All Badges Structure", True, "All badges have required fields")
        
        # Count unlocked badges
        unlocked_badges = [badge for badge in response if badge.get('unlocked', False)]
        unlocked_count = len(unlocked_badges)
        
        # According to review request, at least 2 badges should be unlocked
        if unlocked_count >= 2:
            self.log_test("Unlocked Badges Count", True, f"{unlocked_count} badges unlocked")
            
            # Check for specific badges mentioned in review request
            unlocked_names = [badge['name'] for badge in unlocked_badges]
            expected_unlocked = ["Poupador Iniciante", "Reserva Sólida"]
            
            found_expected = [name for name in expected_unlocked if name in unlocked_names]
            if len(found_expected) >= 2:
                self.log_test("Expected Badges Unlocked", True, f"Found: {found_expected}")
            else:
                self.log_test("Expected Badges Unlocked", False, f"Expected {expected_unlocked}, found: {found_expected}")
                return False
        else:
            self.log_test("Unlocked Badges Count", False, f"Expected at least 2 unlocked badges, got {unlocked_count}")
            return False
        
        return True

    def test_gamification_check_badges(self):
        """Test Check Badges API"""
        success, response = self.run_test(
            "Check and Unlock Badges",
            "POST",
            "gamification/check-badges",
            200
        )
        
        if not success:
            return False
            
        # Verify response structure
        expected_fields = ['unlocked', 'count']
        missing_fields = [field for field in expected_fields if field not in response]
        
        if missing_fields:
            self.log_test("Check Badges Response Structure", False, f"Missing fields: {missing_fields}")
            return False
        else:
            self.log_test("Check Badges Response Structure", True, "All required fields present")
        
        # Verify unlocked is a list
        unlocked = response.get('unlocked', [])
        if isinstance(unlocked, list):
            self.log_test("Check Badges Unlocked List", True, f"Unlocked badges: {len(unlocked)}")
        else:
            self.log_test("Check Badges Unlocked List", False, "Unlocked is not a list")
            return False
        
        # Verify count matches unlocked list length
        count = response.get('count', -1)
        if count == len(unlocked):
            self.log_test("Check Badges Count Match", True, f"Count matches unlocked list: {count}")
        else:
            self.log_test("Check Badges Count Match", False, f"Count {count} doesn't match unlocked list length {len(unlocked)}")
            return False
        
        return True

    def test_gamification_challenges_crud(self):
        """Test Family Challenges CRUD operations"""
        # First, get existing challenges
        success, existing_challenges = self.run_test(
            "Get Existing Challenges",
            "GET",
            "gamification/challenges",
            200
        )
        
        if not success:
            return False
        
        # Check if "Economizar na Energia" challenge exists
        energia_challenge = None
        for challenge in existing_challenges:
            if challenge.get('name') == 'Economizar na Energia':
                energia_challenge = challenge
                break
        
        if energia_challenge:
            self.log_test("Find Energia Challenge", True, f"Found challenge with ID: {energia_challenge['id']}")
        else:
            self.log_test("Find Energia Challenge", False, "Economizar na Energia challenge not found")
        
        # Create a new test challenge
        test_challenge_data = {
            "name": "Test Challenge",
            "description": "Test challenge for automated testing",
            "target_amount": 100.0,
            "reward": "Test reward"
        }
        
        success, create_response = self.run_test(
            "Create Test Challenge",
            "POST",
            "gamification/challenges",
            200,
            data=test_challenge_data
        )
        
        if not success:
            return False
            
        test_challenge_id = create_response.get('id')
        if not test_challenge_id:
            self.log_test("Get Created Challenge ID", False, "No ID returned from create")
            return False
        else:
            self.log_test("Get Created Challenge ID", True, f"Challenge ID: {test_challenge_id}")
        
        # Update challenge progress
        success, progress_response = self.run_test(
            "Update Challenge Progress",
            "POST",
            f"gamification/challenges/{test_challenge_id}/progress?amount=50",
            200
        )
        
        if not success:
            return False
            
        # Verify progress was updated
        current_amount = progress_response.get('current_amount', 0)
        if current_amount == 50:
            self.log_test("Challenge Progress Update", True, f"Progress updated to: {current_amount}")
        else:
            self.log_test("Challenge Progress Update", False, f"Expected 50, got {current_amount}")
            return False
        
        # Delete the test challenge
        success, delete_response = self.run_test(
            "Delete Test Challenge",
            "DELETE",
            f"gamification/challenges/{test_challenge_id}",
            200
        )
        
        if not success:
            return False
        
        # Verify challenge was deleted by trying to get it
        success, get_after_delete = self.run_test(
            "Verify Challenge Deleted",
            "GET",
            "gamification/challenges",
            200
        )
        
        if success:
            # Check that our test challenge is no longer in the list
            remaining_challenges = get_after_delete
            test_challenge_still_exists = any(c.get('id') == test_challenge_id for c in remaining_challenges)
            
            if not test_challenge_still_exists:
                self.log_test("Challenge Deletion Verification", True, "Test challenge successfully deleted")
            else:
                self.log_test("Challenge Deletion Verification", False, "Test challenge still exists after deletion")
                return False
        
        return True

    def test_categorization_rules_crud(self):
        """Test Categorization Rules CRUD operations"""
        # First, get categories to find "Alimentação" category for our test rule
        success, categories_response = self.run_test(
            "Get Categories for Rules Test",
            "GET",
            "categories",
            200
        )
        
        if not success:
            return False
            
        # Find "Alimentação" category
        alimentacao_category = None
        for category in categories_response:
            if category.get('name') == 'Alimentação':
                alimentacao_category = category
                break
        
        if not alimentacao_category:
            self.log_test("Find Alimentação Category", False, "Alimentação category not found")
            return False
        else:
            self.log_test("Find Alimentação Category", True, f"Found category with ID: {alimentacao_category['id']}")
        
        # 1. Test CREATE RULE - Create rule with keyword "mercado" for "Alimentação" category
        rule_data = {
            "keyword": "mercado",
            "category_id": alimentacao_category['id'],
            "match_type": "contains",
            "priority": 10,
            "is_active": True
        }
        
        success, create_response = self.run_test(
            "Create Categorization Rule",
            "POST",
            "categorization-rules",
            200,
            data=rule_data
        )
        
        if not success:
            return False
            
        rule_id = create_response.get('id')
        if not rule_id:
            self.log_test("Get Created Rule ID", False, "No ID returned from create")
            return False
        else:
            self.log_test("Get Created Rule ID", True, f"Rule ID: {rule_id}")
        
        # Verify rule data
        if create_response.get('keyword') == 'mercado' and create_response.get('category_id') == alimentacao_category['id']:
            self.log_test("Rule Creation Data Verification", True, "Rule created with correct data")
        else:
            self.log_test("Rule Creation Data Verification", False, f"Rule data mismatch: {create_response}")
            return False
        
        # 2. Test GET RULES - Should return list of rules sorted by priority
        success, rules_response = self.run_test(
            "Get Categorization Rules",
            "GET",
            "categorization-rules",
            200
        )
        
        if not success:
            return False
            
        # Verify response is a list
        if not isinstance(rules_response, list):
            self.log_test("Rules List Structure", False, "Response is not a list")
            return False
        else:
            self.log_test("Rules List Structure", True, f"Got {len(rules_response)} rules")
        
        # Check if our created rule is in the list
        our_rule = None
        for rule in rules_response:
            if rule.get('id') == rule_id:
                our_rule = rule
                break
        
        if our_rule:
            self.log_test("Find Created Rule in List", True, f"Found rule with keyword: {our_rule.get('keyword')}")
        else:
            self.log_test("Find Created Rule in List", False, "Created rule not found in list")
            return False
        
        # Check if there's an existing "uber" → "Transporte" rule as mentioned in review request
        uber_rule = None
        for rule in rules_response:
            if rule.get('keyword', '').lower() == 'uber':
                uber_rule = rule
                break
        
        if uber_rule:
            self.log_test("Find Uber Rule", True, f"Found uber rule with ID: {uber_rule.get('id')}")
        else:
            self.log_test("Find Uber Rule", False, "Uber → Transporte rule not found (may not exist yet)")
        
        # 3. Test UPDATE RULE - Update keyword or priority
        update_data = {
            "keyword": "supermercado",
            "category_id": alimentacao_category['id'],
            "match_type": "contains",
            "priority": 15,
            "is_active": True
        }
        
        success, update_response = self.run_test(
            "Update Categorization Rule",
            "PUT",
            f"categorization-rules/{rule_id}",
            200,
            data=update_data
        )
        
        if not success:
            return False
        
        # Verify update
        if update_response.get('keyword') == 'supermercado' and update_response.get('priority') == 15:
            self.log_test("Rule Update Verification", True, "Rule updated correctly")
        else:
            self.log_test("Rule Update Verification", False, f"Update failed: {update_response}")
            return False
        
        # 4. Test DELETE RULE
        success, delete_response = self.run_test(
            "Delete Categorization Rule",
            "DELETE",
            f"categorization-rules/{rule_id}",
            200
        )
        
        if not success:
            return False
        
        # Verify deletion by getting rules again
        success, rules_after_delete = self.run_test(
            "Verify Rule Deleted",
            "GET",
            "categorization-rules",
            200
        )
        
        if success:
            # Check that our test rule is no longer in the list
            rule_still_exists = any(r.get('id') == rule_id for r in rules_after_delete)
            
            if not rule_still_exists:
                self.log_test("Rule Deletion Verification", True, "Test rule successfully deleted")
            else:
                self.log_test("Rule Deletion Verification", False, "Test rule still exists after deletion")
                return False
        
        return True

    def test_auto_categorization_on_import(self):
        """Test that auto-categorization works during transaction import"""
        # First, get categories to set up test rules
        success, categories_response = self.run_test(
            "Get Categories for Auto-Categorization Test",
            "GET",
            "categories",
            200
        )
        
        if not success:
            return False
        
        # Find "Transporte" category for uber rule
        transporte_category = None
        for category in categories_response:
            if category.get('name') == 'Transporte':
                transporte_category = category
                break
        
        if not transporte_category:
            self.log_test("Find Transporte Category", False, "Transporte category not found")
            return False
        else:
            self.log_test("Find Transporte Category", True, f"Found category with ID: {transporte_category['id']}")
        
        # Create a test rule for "uber" → "Transporte"
        uber_rule_data = {
            "keyword": "uber",
            "category_id": transporte_category['id'],
            "match_type": "contains",
            "priority": 20,
            "is_active": True
        }
        
        success, uber_rule_response = self.run_test(
            "Create Uber Rule for Auto-Categorization",
            "POST",
            "categorization-rules",
            200,
            data=uber_rule_data
        )
        
        if not success:
            return False
        
        uber_rule_id = uber_rule_response.get('id')
        
        # Get family members and banks for transaction import
        success, members_response = self.run_test(
            "Get Family Members for Import",
            "GET",
            "family",
            200
        )
        
        if not success or not members_response:
            self.log_test("Get Family Members for Import", False, "No family members found")
            return False
        
        success, banks_response = self.run_test(
            "Get Banks for Import",
            "GET",
            "banks",
            200
        )
        
        if not success or not banks_response:
            self.log_test("Get Banks for Import", False, "No banks found")
            return False
        
        member_id = members_response[0]['id']
        bank_id = banks_response[0]['id']
        
        # Create a test CSV with "uber" transaction
        test_csv_content = """Data,Descrição,Valor
2025-01-15,Uber viagem centro,-25.50
2025-01-16,Compra supermercado,-45.00"""
        
        # Test import with auto-categorization
        files = {'file': ('test_transactions.csv', test_csv_content, 'text/csv')}
        form_data = {
            'member_id': member_id,
            'bank_id': bank_id
        }
        
        success, import_response = self.run_test(
            "Import Transactions with Auto-Categorization",
            "POST",
            "transactions/import",
            200,
            data=form_data,
            files=files
        )
        
        if not success:
            # Clean up the rule before returning
            self.run_test("Cleanup Uber Rule", "DELETE", f"categorization-rules/{uber_rule_id}", 200)
            return False
        
        # Check if auto-categorization worked
        auto_categorized = import_response.get('auto_categorized', 0)
        if auto_categorized > 0:
            self.log_test("Auto-Categorization on Import", True, f"{auto_categorized} transactions auto-categorized")
        else:
            self.log_test("Auto-Categorization on Import", False, "No transactions were auto-categorized")
        
        # Verify by getting recent transactions and checking if uber transaction was categorized
        success, transactions_response = self.run_test(
            "Get Transactions to Verify Auto-Categorization",
            "GET",
            "transactions",
            200
        )
        
        if success:
            # Look for the uber transaction
            uber_transaction = None
            for trans in transactions_response:
                if 'uber' in trans.get('description', '').lower():
                    uber_transaction = trans
                    break
            
            if uber_transaction:
                if uber_transaction.get('category_id') == transporte_category['id']:
                    self.log_test("Uber Transaction Categorized", True, f"Uber transaction correctly categorized as Transporte")
                else:
                    self.log_test("Uber Transaction Categorized", False, f"Uber transaction not categorized correctly")
            else:
                self.log_test("Find Uber Transaction", False, "Uber transaction not found in recent transactions")
        
        # Clean up: Delete the test rule
        success, cleanup_response = self.run_test(
            "Cleanup Uber Rule",
            "DELETE",
            f"categorization-rules/{uber_rule_id}",
            200
        )
        
        return True

    def run_gamification_tests(self):
        """Run tests for gamification features specifically"""
        print("🎮 Starting FinFamily Gamification Backend Tests")
        print("=" * 50)
        
        # Test authentication with existing user
        if not self.test_auth_login_existing_user():
            print("❌ Login with test user failed, stopping tests")
            return False
            
        print(f"✅ Authenticated as: {self.user_data.get('name')} ({self.user_data.get('email')})")
        print(f"✅ Admin status: {self.user_data.get('is_admin')}")
        print()
        
        # Test Health Score API
        print("💚 Testing Health Score API...")
        self.test_gamification_health_score()
        print()
        
        # Test Badges API
        print("🏆 Testing Badges API...")
        self.test_gamification_badges()
        print()
        
        # Test Check Badges API
        print("🔍 Testing Check Badges API...")
        self.test_gamification_check_badges()
        print()
        
        # Test Family Challenges CRUD
        print("👨‍👩‍👧‍👦 Testing Family Challenges CRUD...")
        self.test_gamification_challenges_crud()
        print()
        
        # Print summary
        print("=" * 50)
        print(f"📊 Gamification Tests Summary: {self.tests_passed}/{self.tests_run} passed")
        print(f"✅ Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        return self.tests_passed == self.tests_run

    def test_goals_crud(self):
        """Test Goals CRUD operations"""
        # Create goal
        goal_data = {
            "name": "Test Goal",
            "description": "Test goal for automated testing",
            "target_amount": 1000.0,
            "monthly_contribution": 100.0
        }
        success, response = self.run_test(
            "Create Goal",
            "POST",
            "goals",
            200,
            data=goal_data
        )
        
        if not success:
            return False
            
        goal_id = response.get('id')
        
        # Get goals
        success, response = self.run_test(
            "Get Goals",
            "GET",
            "goals",
            200
        )
        
        if not success:
            return False
            
        # Update goal
        update_data = {
            "name": "Updated Test Goal",
            "description": "Updated description",
            "target_amount": 1500.0,
            "monthly_contribution": 150.0
        }
        success, response = self.run_test(
            "Update Goal",
            "PUT",
            f"goals/{goal_id}",
            200,
            data=update_data
        )
        
        if not success:
            return False
            
        # Test goal contribution
        contribution_data = {"amount": 250.0}
        success, response = self.run_test(
            "Add Goal Contribution",
            "POST",
            f"goals/{goal_id}/contribute",
            200,
            data=contribution_data
        )
        
        if not success:
            return False
            
        # Verify contribution was added
        if response.get('current_amount') == 250.0:
            self.log_test("Goal Contribution Verification", True, f"Current amount: {response.get('current_amount')}")
        else:
            self.log_test("Goal Contribution Verification", False, f"Expected 250.0, got {response.get('current_amount')}")
            return False
        
        # Delete goal
        success, response = self.run_test(
            "Delete Goal",
            "DELETE",
            f"goals/{goal_id}",
            200
        )
        
        return success

    def test_transactions_crud_and_filters(self):
        """Test transaction CRUD operations and filtering"""
        # Get existing transactions for filtering tests
        success, all_transactions = self.run_test(
            "Get All Transactions",
            "GET",
            "transactions",
            200
        )
        
        if not success:
            return False
            
        # Test month/year filtering
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        success, filtered_transactions = self.run_test(
            "Get Transactions with Month/Year Filter",
            "GET",
            f"transactions?month={current_month}&year={current_year}",
            200
        )
        
        if not success:
            return False
            
        # Verify filtering worked (should be <= all transactions)
        if len(filtered_transactions) <= len(all_transactions):
            self.log_test("Transaction Month/Year Filter", True, f"Filtered: {len(filtered_transactions)}, Total: {len(all_transactions)}")
        else:
            self.log_test("Transaction Month/Year Filter", False, f"Filtered count {len(filtered_transactions)} > total {len(all_transactions)}")
            return False
        
        # Test bulk categorization if we have transactions and categories
        if filtered_transactions:
            # Get categories
            success, categories = self.run_test(
                "Get Categories for Bulk Categorization",
                "GET",
                "categories",
                200
            )
            
            if success and categories:
                # Use first category and first transaction
                category_id = categories[0]['id']
                transaction_id = filtered_transactions[0]['id']
                
                bulk_data = {
                    "transaction_ids": [transaction_id],
                    "category_id": category_id
                }
                
                success, response = self.run_test(
                    "Bulk Categorize Transactions",
                    "POST",
                    "transactions/bulk-categorize",
                    200,
                    data=bulk_data
                )
                
                if success:
                    count = response.get('count', 0)
                    if count == 1:
                        self.log_test("Bulk Categorization Count", True, f"Categorized {count} transaction")
                    else:
                        self.log_test("Bulk Categorization Count", False, f"Expected 1, got {count}")
                        return False
        
        return True

    def test_emergency_reserve_api(self):
        """Test Emergency Reserve API specifically"""
        success, response = self.run_test(
            "Get Emergency Reserve",
            "GET",
            "dashboard/emergency-reserve",
            200
        )
        
        if not success:
            return False
            
        # Verify response structure
        if 'total' not in response:
            self.log_test("Emergency Reserve Structure", False, "Missing 'total' field")
            return False
        else:
            self.log_test("Emergency Reserve Structure", True, f"Total: R$ {response['total']}")
        
        # According to review request, should be R$ 2.000,00
        total = response.get('total', 0)
        if total == 2000.0:
            self.log_test("Emergency Reserve Amount", True, f"Correct amount: R$ {total}")
        else:
            self.log_test("Emergency Reserve Amount", False, f"Expected R$ 2000.0, got R$ {total}")
        
        return True

    def test_complete_dashboard_apis(self):
        """Test all dashboard APIs comprehensively"""
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Test emergency reserve
        if not self.test_emergency_reserve_api():
            return False
        
        # Test dashboard summary
        success, response = self.run_test(
            "Dashboard Summary",
            "GET",
            f"dashboard/summary?month={current_month}&year={current_year}",
            200
        )
        
        if not success:
            return False
            
        # Verify summary structure
        expected_fields = ['previous_balance', 'month_income', 'month_expenses', 'final_balance']
        missing_fields = [field for field in expected_fields if field not in response]
        
        if missing_fields:
            self.log_test("Dashboard Summary Structure", False, f"Missing fields: {missing_fields}")
            return False
        else:
            self.log_test("Dashboard Summary Structure", True, "All required fields present")
        
        # Test category chart
        success, response = self.run_test(
            "Category Chart Data",
            "GET",
            f"dashboard/category-chart?month={current_month}&year={current_year}",
            200
        )
        
        if not success:
            return False
            
        # Verify it's a list
        if isinstance(response, list):
            self.log_test("Category Chart Structure", True, f"Got {len(response)} categories")
        else:
            self.log_test("Category Chart Structure", False, "Response is not a list")
            return False
        
        # Test monthly comparison
        success, response = self.run_test(
            "Monthly Comparison Data",
            "GET",
            f"dashboard/monthly-comparison?year={current_year}",
            200
        )
        
        if not success:
            return False
            
        # Verify it's a list with 12 months
        if isinstance(response, list) and len(response) == 12:
            self.log_test("Monthly Comparison Structure", True, f"Got {len(response)} months")
        else:
            self.log_test("Monthly Comparison Structure", False, f"Expected 12 months, got {len(response) if isinstance(response, list) else 'not a list'}")
            return False
        
        return True

    def test_auth_register_new_user(self):
        """Test user registration with new user"""
        test_email = f"test_{uuid.uuid4().hex[:8]}@finamily.com"
        test_data = {
            "email": test_email,
            "password": "TestPass123!",
            "name": "Test User Registration"
        }
        
        # Since first user is admin, this should return 202 (waiting for approval)
        success, response = self.run_test(
            "User Registration (New User)",
            "POST",
            "auth/register",
            202,  # Expecting 202 for non-first user
            data=test_data
        )
        
        return success

    def test_invalid_login(self):
        """Test login with invalid credentials"""
        invalid_data = {
            "email": "invalid@example.com",
            "password": "wrongpassword"
        }
        
        success, response = self.run_test(
            "Login with Invalid Credentials",
            "POST",
            "auth/login",
            401,  # Should fail with 401
            data=invalid_data
        )
        
        return success

    def test_transaction_individual_operations(self):
        """Test individual transaction operations (create, update, delete)"""
        # Get family members and banks first
        success, members = self.run_test("Get Members for Transaction Test", "GET", "family", 200)
        if not success or not members:
            self.log_test("Get Members for Transaction Test", False, "No family members found")
            return False
            
        success, banks = self.run_test("Get Banks for Transaction Test", "GET", "banks", 200)
        if not success or not banks:
            self.log_test("Get Banks for Transaction Test", False, "No banks found")
            return False
        
        # Create a test transaction
        transaction_data = {
            "date": datetime.now().isoformat(),
            "description": "Test Transaction for CRUD",
            "amount": 100.0,
            "type": "despesa",
            "member_id": members[0]['id'],
            "bank_id": banks[0]['id']
        }
        
        # Note: We can't directly create transactions via POST /transactions endpoint
        # as it's not implemented in the backend. Transactions are created via import.
        # So we'll test getting a specific transaction instead
        
        # Get all transactions first
        success, transactions = self.run_test("Get Transactions for Individual Test", "GET", "transactions", 200)
        if not success or not transactions:
            self.log_test("Get Transactions for Individual Test", False, "No transactions found")
            return False
        
        # Test getting a specific transaction
        transaction_id = transactions[0]['id']
        success, response = self.run_test(
            "Get Individual Transaction",
            "GET",
            f"transactions/{transaction_id}",
            200
        )
        
        if not success:
            return False
        
        # Test updating the transaction
        update_data = {
            "date": response['date'],
            "description": "Updated Test Transaction",
            "amount": response['amount'],
            "type": response['type'],
            "member_id": response['member_id'],
            "bank_id": response['bank_id']
        }
        
        success, updated_response = self.run_test(
            "Update Transaction",
            "PUT",
            f"transactions/{transaction_id}",
            200,
            data=update_data
        )
        
        if not success:
            return False
        
        # Verify update
        if updated_response.get('description') == "Updated Test Transaction":
            self.log_test("Transaction Update Verification", True, "Description updated correctly")
        else:
            self.log_test("Transaction Update Verification", False, f"Expected 'Updated Test Transaction', got '{updated_response.get('description')}'")
            return False
        
        # Test deleting the transaction (we'll restore it by updating back)
        # Actually, let's not delete as it might affect other tests
        # Instead, restore the original description
        restore_data = {
            "date": response['date'],
            "description": response['description'],  # Original description
            "amount": response['amount'],
            "type": response['type'],
            "member_id": response['member_id'],
            "bank_id": response['bank_id']
        }
        
        success, restored_response = self.run_test(
            "Restore Transaction Description",
            "PUT",
            f"transactions/{transaction_id}",
            200,
            data=restore_data
        )
        
        return success

    def run_complete_backend_tests(self):
        """Run COMPLETE test of ALL FinFamily backend endpoints"""
        print("🚀 COMPLETE FinFamily Backend API Testing")
        print("=" * 60)
        
        # Reset counters for complete test
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # 1. AUTHENTICATION TESTS
        print("🔐 1. TESTING AUTHENTICATION...")
        if not self.test_auth_login_existing_user():
            print("❌ Login with test user failed, stopping tests")
            return False
            
        print(f"✅ Authenticated as: {self.user_data.get('name')} ({self.user_data.get('email')})")
        print(f"✅ Admin status: {self.user_data.get('is_admin')}")
        
        # Test registration
        self.test_auth_register_new_user()
        self.test_invalid_login()
        print()
        
        # 2. FAMILY, BANKS, CATEGORIES CRUD
        print("👨‍👩‍👧‍👦 2. TESTING FAMILY, BANKS, CATEGORIES CRUD...")
        self.test_family_crud()
        self.test_banks_crud()
        self.test_categories_crud()
        print()
        
        # 3. TRANSACTIONS
        print("💳 3. TESTING TRANSACTIONS...")
        self.test_transactions_crud_and_filters()
        self.test_transaction_individual_operations()
        self.test_transactions_with_category_filter()
        print()
        
        # 4. DASHBOARD
        print("📊 4. TESTING DASHBOARD...")
        self.test_complete_dashboard_apis()
        print()
        
        # 5. GOALS (METAS)
        print("🎯 5. TESTING GOALS (METAS)...")
        self.test_goals_crud()
        print()
        
        # 6. PROFILE
        print("👤 6. TESTING PROFILE...")
        self.test_profile_endpoints()
        self.test_change_password_endpoint()
        self.test_delete_all_transactions_endpoint()
        print()
        
        # 7. GAMIFICATION
        print("🎮 7. TESTING GAMIFICATION...")
        self.test_gamification_health_score()
        self.test_gamification_badges()
        self.test_gamification_check_badges()
        self.test_gamification_challenges_crud()
        print()
        
        # 8. CATEGORIZATION RULES
        print("🏷️ 8. TESTING CATEGORIZATION RULES...")
        self.test_categorization_rules_crud()
        self.test_auto_categorization_on_import()
        print()
        
        # Print final summary
        print("=" * 60)
        print(f"📊 COMPLETE BACKEND TESTS SUMMARY")
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Show failed tests
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        else:
            print("\n✅ ALL TESTS PASSED!")
        
        return self.tests_passed == self.tests_run

    def run_new_features_tests(self):
        """Run tests for new features specifically mentioned in review request"""
        print("🚀 Starting FinFamily New Features Backend Tests")
        print("=" * 50)
        
        # Test authentication with existing user
        if not self.test_auth_login_existing_user():
            print("❌ Login with test user failed, stopping tests")
            return False
            
        print(f"✅ Authenticated as: {self.user_data.get('name')} ({self.user_data.get('email')})")
        print(f"✅ Admin status: {self.user_data.get('is_admin')}")
        print()
        
        # Test new profile endpoints
        print("📋 Testing Profile Endpoints...")
        self.test_profile_endpoints()
        print()
        
        # Test password change endpoint
        print("🔒 Testing Password Change...")
        self.test_change_password_endpoint()
        print()
        
        # Test delete all transactions endpoint existence
        print("🗑️ Testing Delete All Transactions Endpoint...")
        self.test_delete_all_transactions_endpoint()
        print()
        
        # Test category filtering for transactions
        print("🏷️ Testing Category Filter for Transactions...")
        self.test_transactions_with_category_filter()
        print()
        
        # Print summary
        print("=" * 50)
        print(f"📊 New Features Tests Summary: {self.tests_passed}/{self.tests_run} passed")
        print(f"✅ Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = FinancialAppTester()
    
    # Run COMPLETE backend tests as requested in review
    success = tester.run_complete_backend_tests()
    
    # Save detailed results
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "test_type": "complete_backend_testing",
            "total_tests": tester.tests_run,
            "passed_tests": tester.tests_passed,
            "success_rate": (tester.tests_passed/tester.tests_run)*100 if tester.tests_run > 0 else 0,
            "results": tester.test_results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())