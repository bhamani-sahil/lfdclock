#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timezone, timedelta

class LFDClockAPITester:
    def __init__(self, base_url="https://logistics-lfd.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_email = f"test_user_{datetime.now().strftime('%H%M%S')}@testcompany.com"
        self.test_password = "TestPass123!"
        self.test_company = f"Test Logistics {datetime.now().strftime('%H%M%S')}"

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - Status: {response.status_code}")
                try:
                    resp_data = response.json() if response.content else {}
                    if resp_data and len(str(resp_data)) < 500:  # Only show short responses
                        print(f"   Response: {resp_data}")
                    return True, resp_data
                except:
                    return True, {}
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json() if response.content else {}
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Raw response: {response.text[:200]}")
                return False, {}

        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test API health check"""
        success, _ = self.run_test("Health Check", "GET", "health", 200)
        return success

    def test_signup(self):
        """Test user signup"""
        success, response = self.run_test(
            "User Signup",
            "POST", 
            "auth/signup",
            200,
            data={
                "email": self.test_email,
                "password": self.test_password,
                "company_name": self.test_company,
                "phone": "+1-555-123-4567"
            }
        )
        if success and 'token' in response and 'user' in response:
            self.token = response['token']
            self.user_id = response['user']['id']
            print(f"   🔑 Token acquired: {self.token[:20]}...")
            print(f"   👤 User ID: {self.user_id}")
            print(f"   📧 Forwarding email: {response['user'].get('forwarding_email', 'N/A')}")
            return True
        return False

    def test_login(self):
        """Test user login"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login", 
            200,
            data={
                "email": self.test_email,
                "password": self.test_password
            }
        )
        if success and 'token' in response:
            new_token = response['token']
            print(f"   🔑 Login token: {new_token[:20]}...")
            return True
        return False

    def test_get_me(self):
        """Test get current user"""
        success, response = self.run_test("Get Current User", "GET", "auth/me", 200)
        if success:
            print(f"   👤 User: {response.get('email')} | {response.get('company_name')}")
        return success

    def test_get_shipments(self):
        """Test get shipments (should be empty initially)"""
        success, response = self.run_test("Get Shipments", "GET", "shipments", 200)
        if success:
            print(f"   📦 Shipments count: {len(response)}")
        return success

    def test_get_shipment_stats(self):
        """Test get shipment stats"""
        success, response = self.run_test("Get Shipment Stats", "GET", "shipments/stats", 200)
        if success:
            print(f"   📊 Stats: {response}")
        return success

    def test_create_shipment(self):
        """Test create shipment"""
        now = datetime.now(timezone.utc)
        arrival_date = (now - timedelta(days=2)).isoformat()
        lfd_date = (now + timedelta(hours=48)).isoformat()  # Safe status
        
        success, response = self.run_test(
            "Create Shipment",
            "POST",
            "shipments",
            200,
            data={
                "container_number": "TEST1234567",
                "vessel_name": "Test Vessel",
                "arrival_date": arrival_date,
                "last_free_day": lfd_date,
                "notes": "Test shipment for API testing"
            }
        )
        if success:
            print(f"   📦 Created shipment: {response.get('container_number')} | Status: {response.get('status')}")
            return response.get('id')
        return None

    def test_delete_shipment(self, shipment_id):
        """Test delete shipment"""
        if not shipment_id:
            print("❌ No shipment ID provided for deletion test")
            return False
        
        success, _ = self.run_test("Delete Shipment", "DELETE", f"shipments/{shipment_id}", 200)
        return success

    def test_seed_demo_data(self):
        """Test seed demo data"""
        success, response = self.run_test("Seed Demo Data", "POST", "demo/seed", 200)
        if success:
            print(f"   🎯 Demo shipments created: {len(response.get('shipments', []))}")
        return success

    def test_notification_settings(self):
        """Test notification settings"""
        # Get settings
        get_success, settings = self.run_test("Get Notification Settings", "GET", "settings/notifications", 200)
        
        if not get_success:
            return False

        # Update settings
        update_success, _ = self.run_test(
            "Update Notification Settings",
            "PUT",
            "settings/notifications",
            200,
            data={"notify_48h": False, "notify_6h": True}
        )
        
        return update_success

    def test_email_parsing(self):
        """Test email parsing (simulated)"""
        success, response = self.run_test(
            "Email Parsing (Simulated)",
            "POST",
            "email/parse",
            200,
            data={
                "subject": "Container Release Notice - MSCU1234567",
                "body": "Container MSCU1234567 on vessel MSC AURORA has arrived. Last Free Day: 2024-12-20T15:00:00Z",
                "from_email": "noreply@msclines.com"
            }
        )
        if success:
            shipment_data = response.get('shipment', {})
            print(f"   🤖 Parsed: {shipment_data.get('container_number')} | Status: {shipment_data.get('status')}")
        return success

    def test_notification_logs(self):
        """Test get notification logs"""
        success, response = self.run_test("Get Notification Logs", "GET", "notifications/logs", 200)
        if success:
            print(f"   📱 SMS logs count: {len(response)}")
        return success

    def test_check_notifications(self):
        """Test check and send notifications"""
        success, response = self.run_test("Check Notifications", "POST", "notifications/check", 200)
        if success:
            notifications = response.get('notifications', [])
            print(f"   🔔 Notifications sent: {len(notifications)}")
        return success

def main():
    """Run all API tests"""
    print("🚀 Starting LFD Clock API Tests")
    print("=" * 50)
    
    tester = LFDClockAPITester()
    
    # Test sequence
    tests = [
        ("Health Check", tester.test_health_check),
        ("User Signup", tester.test_signup),
        ("User Login", tester.test_login),
        ("Get Current User", tester.test_get_me),
        ("Get Initial Shipments", tester.test_get_shipments),
        ("Get Initial Stats", tester.test_get_shipment_stats),
        ("Create Shipment", lambda: tester.test_create_shipment()),
        ("Seed Demo Data", tester.test_seed_demo_data),
        ("Get Updated Shipments", tester.test_get_shipments),
        ("Get Updated Stats", tester.test_get_shipment_stats),
        ("Notification Settings", tester.test_notification_settings),
        ("Notification Logs", tester.test_notification_logs),
        ("Check Notifications", tester.test_check_notifications),
        ("Email Parsing", tester.test_email_parsing),
    ]
    
    shipment_id = None
    for test_name, test_func in tests:
        try:
            result = test_func()
            if test_name == "Create Shipment" and result:
                shipment_id = result
        except Exception as e:
            print(f"❌ EXCEPTION in {test_name}: {str(e)}")
    
    # Test shipment deletion if we created one
    if shipment_id:
        tester.test_delete_shipment(shipment_id)

    # Print final results
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    print(f"Total tests: {tester.tests_run}")
    print(f"Passed: {tester.tests_passed}")
    print(f"Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())