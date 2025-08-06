"""
API testing script for Chime Dashboard backend.
"""
import requests
import json
import os
from typing import Optional

# Base URL for API
BASE_URL = "http://localhost:8100"


class ChimeDashboardAPITester:
    """API tester class for Chime Dashboard."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.session = requests.Session()
    
    def set_auth_header(self):
        """Set authorization header with access token."""
        if self.access_token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.access_token}"
            })
    
    def test_health_check(self):
        """Test health check endpoint."""
        print("\n=== Testing Health Check ===")
        try:
            response = requests.get(f"{self.base_url}/health")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def test_login(self, email: str = "admin@chimei.com", password: str = "admin123"):
        """Test user login."""
        print("\n=== Testing Login ===")
        try:
            data = {
                "email": email,
                "password": password
            }
            response = requests.post(f"{self.base_url}/api/auth/login", json=data)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result["access_token"]
                self.set_auth_header()
                print("Login successful!")
                print(f"Access token: {self.access_token[:50]}...")
                return True
            else:
                print(f"Login failed: {response.text}")
                return False
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def test_get_current_user(self):
        """Test get current user info."""
        print("\n=== Testing Get Current User ===")
        try:
            response = self.session.get(f"{self.base_url}/api/auth/me")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                user_info = response.json()
                print(f"User info: {json.dumps(user_info, indent=2, ensure_ascii=False)}")
                return True
            else:
                print(f"Failed: {response.text}")
                return False
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def test_get_users(self):
        """Test get users list."""
        print("\n=== Testing Get Users ===")
        try:
            response = self.session.get(f"{self.base_url}/api/users/")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                users = response.json()
                print(f"Users count: {len(users.get('items', []))}")
                print(f"Total: {users.get('total', 0)}")
                return True
            else:
                print(f"Failed: {response.text}")
                return False
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def test_get_product_labels(self):
        """Test get product labels."""
        print("\n=== Testing Get Product Labels ===")
        try:
            response = self.session.get(f"{self.base_url}/api/labels/products")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                labels = response.json()
                print(f"Product labels count: {len(labels)}")
                if labels:
                    print(f"First label: {labels[0]}")
                return True
            else:
                print(f"Failed: {response.text}")
                return False
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def test_get_feedback_categories(self):
        """Test get feedback categories."""
        print("\n=== Testing Get Feedback Categories ===")
        try:
            response = self.session.get(f"{self.base_url}/api/labels/categories")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                categories = response.json()
                print(f"Feedback categories count: {len(categories)}")
                if categories:
                    print(f"First category: {categories[0]}")
                return True
            else:
                print(f"Failed: {response.text}")
                return False
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def test_create_product_label(self, name: str = "測試產品"):
        """Test create product label."""
        print(f"\n=== Testing Create Product Label: {name} ===")
        try:
            data = {
                "name": name,
                "description": f"{name}的描述",
                "is_active": True
            }
            response = self.session.post(f"{self.base_url}/api/labels/products", json=data)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                label = response.json()
                print(f"Created label: {json.dumps(label, indent=2, ensure_ascii=False)}")
                return label["id"]
            else:
                print(f"Failed: {response.text}")
                return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def test_file_upload(self, file_path: str = None):
        """Test file upload."""
        print("\n=== Testing File Upload ===")
        
        # Create a test text file if none provided
        if not file_path:
            test_content = "這是一個測試文件內容。客戶反映水餃的味道很好，但是包裝有問題。"
            test_file_path = "/tmp/test_feedback.txt"
            
            try:
                with open(test_file_path, "w", encoding="utf-8") as f:
                    f.write(test_content)
                file_path = test_file_path
                print(f"Created test file: {file_path}")
            except Exception as e:
                print(f"Failed to create test file: {e}")
                return None
        
        try:
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f, "text/plain")}
                response = self.session.post(f"{self.base_url}/api/files/upload", files=files)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Upload result: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return result.get("file_id")
            else:
                print(f"Failed: {response.text}")
                return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def test_get_files(self):
        """Test get files list."""
        print("\n=== Testing Get Files ===")
        try:
            response = self.session.get(f"{self.base_url}/api/files/")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                files_data = response.json()
                print(f"Files count: {len(files_data.get('items', []))}")
                print(f"Total: {files_data.get('total', 0)}")
                return True
            else:
                print(f"Failed: {response.text}")
                return False
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def test_dashboard_data(self):
        """Test dashboard data endpoint."""
        print("\n=== Testing Dashboard Data ===")
        try:
            response = self.session.get(f"{self.base_url}/api/data/dashboard")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                dashboard_data = response.json()
                print(f"Dashboard data: {json.dumps(dashboard_data, indent=2, ensure_ascii=False)}")
                return True
            else:
                print(f"Failed: {response.text}")
                return False
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all API tests."""
        print("Starting Chime Dashboard API Tests...")
        print(f"Base URL: {self.base_url}")
        
        results = {}
        
        # Basic tests
        results["health_check"] = self.test_health_check()
        results["login"] = self.test_login()
        
        if not results["login"]:
            print("\nLogin failed, skipping authenticated tests...")
            return results
        
        # Authenticated tests
        results["get_current_user"] = self.test_get_current_user()
        results["get_users"] = self.test_get_users()
        results["get_product_labels"] = self.test_get_product_labels()
        results["get_feedback_categories"] = self.test_get_feedback_categories()
        results["create_product_label"] = self.test_create_product_label() is not None
        results["file_upload"] = self.test_file_upload() is not None
        results["get_files"] = self.test_get_files()
        results["dashboard_data"] = self.test_dashboard_data()
        
        # Print summary
        print("\n" + "="*50)
        print("TEST SUMMARY")
        print("="*50)
        
        for test_name, result in results.items():
            status = "PASS" if result else "FAIL"
            print(f"{test_name:25} {status}")
        
        total_tests = len(results)
        passed_tests = sum(results.values())
        print(f"\nTotal: {total_tests}, Passed: {passed_tests}, Failed: {total_tests - passed_tests}")
        
        return results


def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Chime Dashboard API Tester")
    parser.add_argument("--url", default=BASE_URL, help="Base URL for API")
    parser.add_argument("--test", help="Specific test to run")
    
    args = parser.parse_args()
    
    tester = ChimeDashboardAPITester(args.url)
    
    if args.test:
        # Run specific test
        test_method = getattr(tester, f"test_{args.test}", None)
        if test_method:
            # Login first for authenticated tests
            if args.test != "health_check":
                tester.test_login()
            test_method()
        else:
            print(f"Test '{args.test}' not found")
    else:
        # Run all tests
        tester.run_all_tests()


if __name__ == "__main__":
    main()