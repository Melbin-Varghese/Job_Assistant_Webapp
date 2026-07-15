#!/usr/bin/env python3
"""
Test script for CareerMomentum Email Automation
Run this to verify everything works without sending real emails
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:5000"
TEST_USER_EMAIL = "akshaykunjumon8606@gmail.com"
TEST_COMPANY = "Luminar"
TEST_JOB_ROLE = "Data Analyst"
TEST_HR_EMAILS = ["hr@luminar.com", "career@luminar.com"]

def print_header(title):
    """Print section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_health_check():
    """Test if server is running"""
    print_header("1️⃣  Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Server is running")
            print(f"✓ Gmail API: {'Available' if data.get('gmail_available') else 'Not installed (using mock)'}")
            print(f"✓ Database: {'Ready' if data.get('database') else 'Missing'}")
            return True
        else:
            print(f"✗ Server returned: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"✗ Cannot connect to {BASE_URL}")
        print("   Make sure Flask is running: python app_fixed.py")
        return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_send_applications():
    """Test sending applications"""
    print_header("2️⃣  Send Applications Test")
    
    payload = {
        "user_email": TEST_USER_EMAIL,
        "company": TEST_COMPANY,
        "job_role": TEST_JOB_ROLE,
        "hr_emails": TEST_HR_EMAILS,
        "cover_letter_body": "I am writing to express my interest in the {role} position at {company}. With my AI/ML background and hands-on experience, I'm confident I can contribute meaningfully to your team. Thank you for considering my application.".replace("{role}", TEST_JOB_ROLE).replace("{company}", TEST_COMPANY),
        "subject": f"Data Analyst Application - SQL & Analytics at {TEST_COMPANY}",
        "cv_path": None
    }
    
    print(f"Sending test email...")
    print(f"  Company: {TEST_COMPANY}")
    print(f"  Job Role: {TEST_JOB_ROLE}")
    print(f"  Recipients: {len(TEST_HR_EMAILS)}")
    print(f"  Subject: {payload['subject']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/send-applications",
            json=payload,
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✓ Success!")
                print(f"✓ Sent to {data.get('sent_count')}/{data.get('total_count')} recipients")
                print(f"✓ Message: {data.get('message')}")
                
                # Show results per email
                print(f"\nResults:")
                for result in data.get('results', []):
                    status = "✓" if result.get('success') else "✗"
                    print(f"  {status} {result.get('hr_email')}: {result.get('message')}")
                
                return True
            else:
                print(f"✗ Failed: {data.get('error')}")
                return False
        else:
            print(f"✗ Server error: {response.status_code}")
            try:
                print(f"Response: {response.json()}")
            except:
                print(f"Response: {response.text}")
            return False
    
    except requests.exceptions.Timeout:
        print(f"✗ Request timeout")
        return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_get_history():
    """Test getting application history"""
    print_header("3️⃣  Application History Test")
    
    print(f"Fetching history for: {TEST_USER_EMAIL}")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/applications-history",
            params={"email": TEST_USER_EMAIL},
            timeout=10
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                apps = data.get('applications', [])
                print(f"✓ Found {len(apps)} application(s)")
                
                if len(apps) > 0:
                    print(f"\nLatest applications:")
                    for app in apps[:5]:  # Show first 5
                        print(f"  • {app.get('company')} - {app.get('job_role')}")
                        print(f"    To: {app.get('hr_email')}")
                        print(f"    Status: {app.get('email_status')}")
                        print(f"    Sent: {app.get('sent_at')}")
                else:
                    print(f"  (No applications found yet)")
                
                return True
            else:
                print(f"✗ Failed: {data.get('error')}")
                return False
        else:
            print(f"✗ Server error: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_validation():
    """Test validation errors"""
    print_header("4️⃣  Validation Test")
    
    test_cases = [
        {
            "name": "Missing required fields",
            "payload": {
                "user_email": TEST_USER_EMAIL,
                # Missing: company, job_role, hr_emails, cover_letter_body
            },
            "should_fail": True
        },
        {
            "name": "Invalid email format",
            "payload": {
                "user_email": "not-an-email",
                "company": TEST_COMPANY,
                "job_role": TEST_JOB_ROLE,
                "hr_emails": ["invalid-email"],
                "cover_letter_body": "Test"
            },
            "should_fail": True
        },
        {
            "name": "Empty HR emails list",
            "payload": {
                "user_email": TEST_USER_EMAIL,
                "company": TEST_COMPANY,
                "job_role": TEST_JOB_ROLE,
                "hr_emails": [],
                "cover_letter_body": "Test"
            },
            "should_fail": True
        }
    ]
    
    passed = 0
    for test in test_cases:
        try:
            response = requests.post(
                f"{BASE_URL}/api/send-applications",
                json=test.get('payload'),
                timeout=10
            )
            
            data = response.json()
            success = data.get('success', False)
            
            # Check if result matches expectation
            if test.get('should_fail') and not success:
                print(f"✓ {test.get('name')}")
                print(f"  Error: {data.get('error')}")
                passed += 1
            elif not test.get('should_fail') and success:
                print(f"✓ {test.get('name')}")
                passed += 1
            else:
                print(f"✗ {test.get('name')}")
                print(f"  Expected: {'fail' if test.get('should_fail') else 'success'}")
                print(f"  Got: {'success' if success else 'fail'}")
        
        except Exception as e:
            print(f"✗ {test.get('name')}: {str(e)}")
    
    return passed == len(test_cases)

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  CareerMomentum Email Automation - Test Suite".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    
    results = {
        "Health Check": test_health_check(),
        "Send Applications": test_send_applications(),
        "Application History": test_get_history(),
        "Validation": test_validation()
    }
    
    # Summary
    print_header("📊 Test Summary")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n" + "=" * 60)
        print("🎉 All tests passed! Email automation is working!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Go to http://127.0.0.1:5000")
        print("2. Fill in your job details")
        print("3. Generate cover letter")
        print("4. Add HR emails")
        print("5. Send applications")
    else:
        print("\n" + "=" * 60)
        print("⚠️  Some tests failed. Check errors above.")
        print("=" * 60)
        print("\nTroubleshooting:")
        print("1. Is Flask running? (python app_fixed.py)")
        print("2. Is it on port 5000? (or update BASE_URL)")
        print("3. Check Flask console for error messages")
    
    return passed == total

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)