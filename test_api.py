import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_endpoint(name, method, url, data=None):
    """Test an API endpoint"""
    print(f"\n{'='*70}")
    print(f"TEST: {name}")
    print(f"{'='*70}")
    print(f"Method: {method}")
    print(f"URL: {url}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
            print(f"Request Body: {json.dumps(data, indent=2)}")
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS")
            print(f"\nResponse:")
            print(json.dumps(result, indent=2)[:500])  # First 500 chars
            if len(json.dumps(result)) > 500:
                print("... (truncated)")
            return True
        else:
            print(f"❌ FAILED")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ CONNECTION ERROR - Is the server running?")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def run_all_tests():
    """Run all API tests"""
    print("\n" + "="*70)
    print("🧪 STARTING API TESTS")
    print("="*70)
    print(f"API Base URL: {API_BASE}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    results = []
    
    # Test 1: Health Check
    results.append(test_endpoint(
        "Health Check",
        "GET",
        f"{API_BASE}/"
    ))
    
    time.sleep(1)
    
    # Test 2: Natural Language Query - Show Python Students
    results.append(test_endpoint(
        "Natural Language Query - Python Students",
        "POST",
        f"{API_BASE}/api/query",
        {"query": "Show students who know Python"}
    ))
    
    time.sleep(1)
    
    # Test 3: Natural Language Query - Course Recommendation
    results.append(test_endpoint(
        "Natural Language Query - Course Recommendations",
        "POST",
        f"{API_BASE}/api/query",
        {"query": "Recommend courses for machine learning"}
    ))
    
    time.sleep(1)
    
    # Test 4: Natural Language Query - Internships
    results.append(test_endpoint(
        "Natural Language Query - Internship Requirements",
        "POST",
        f"{API_BASE}/api/query",
        {"query": "Which internships require Python and SQL?"}
    ))
    
    time.sleep(1)
    
    # Test 5: Get Student Profile
    results.append(test_endpoint(
        "Get Student Profile (S001)",
        "GET",
        f"{API_BASE}/api/student/S001"
    ))
    
    time.sleep(1)
    
    # Test 6: Course Recommendations by Skill
    results.append(test_endpoint(
        "Course Recommendations for Python",
        "GET",
        f"{API_BASE}/api/courses?skill=Python"
    ))
    
    time.sleep(1)
    
    # Test 7: Course Recommendations for Student
    results.append(test_endpoint(
        "Personalized Course Recommendations (S004)",
        "GET",
        f"{API_BASE}/api/courses?student_id=S004"
    ))
    
    time.sleep(1)
    
    # Test 8: Internship Recommendations
    results.append(test_endpoint(
        "Internship Recommendations (S002)",
        "GET",
        f"{API_BASE}/api/internships/S002"
    ))
    
    time.sleep(1)
    
    # Test 9: Skill Gap Analysis
    results.append(test_endpoint(
        "Skill Gap Analysis (S001 → I001)",
        "GET",
        f"{API_BASE}/api/skill-gap?student_id=S001&internship_id=I001"
    ))
    
    time.sleep(1)
    
    # Test 10: Search Students by Skill
    results.append(test_endpoint(
        "Search Students with Python Skill",
        "GET",
        f"{API_BASE}/api/students/search?skill=Python"
    ))
    
    time.sleep(1)
    
    # Test 11: Search Students by Major
    results.append(test_endpoint(
        "Search Students in Data Science",
        "GET",
        f"{API_BASE}/api/students/search?major=Data Science"
    ))
    
    time.sleep(1)
    
    # Test 12: Search Students by GPA
    results.append(test_endpoint(
        "Search Students with GPA >= 3.5",
        "GET",
        f"{API_BASE}/api/students/search?min_gpa=3.5"
    ))
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {total - passed} ❌")
    print(f"Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    # Check if server is running
    print("\n⏳ Checking if API server is running...")
    try:
        response = requests.get(f"{API_BASE}/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running!\n")
            run_all_tests()
        else:
            print("❌ Server returned unexpected status")
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API server!")
        print("\n🔧 Please start the server first:")
        print("   python app.py")
        print("\nThen run this test script again.\n")
    except Exception as e:
        print(f"❌ Error: {e}")