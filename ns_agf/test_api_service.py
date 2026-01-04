"""
Test NS-AGF API Service
========================

Quick test script to verify the API endpoints are working correctly.

Usage:
    1. Start the API service: python api_service.py
    2. Run this test: python test_api_service.py
"""

import requests
import json
import base64
import cv2
import numpy as np

API_URL = "http://127.0.0.1:5002"


def test_health():
    """Test health check endpoint"""
    print("\n" + "=" * 70)
    print("TEST 1: Health Check")
    print("=" * 70)
    
    try:
        response = requests.get(f"{API_URL}/api/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check PASSED")
            print(f"   Status: {data.get('status')}")
            print(f"   Service: {data.get('service')}")
            print(f"   Inference ready: {data.get('inference_ready')}")
            print(f"   Biometric ready: {data.get('biometric_ready')}")
            print(f"   Enrolled users: {data.get('enrolled_users')}")
            return True
        else:
            print(f"❌ Health check FAILED: Status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API service")
        print("   Make sure the service is running: python api_service.py")
        return False
    except Exception as e:
        print(f"❌ Health check FAILED: {e}")
        return False


def test_sign_recognition():
    """Test sign recognition endpoint with dummy frames"""
    print("\n" + "=" * 70)
    print("TEST 2: Sign Recognition")
    print("=" * 70)
    
    try:
        # Create dummy frames (simple colored images)
        frames = []
        print("   Creating 20 dummy frames...")
        
        for i in range(20):
            # Create a simple colored frame
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            color = int(255 * (i / 20))
            frame[:, :] = [color, 100, 200]
            
            # Encode to JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            
            # Convert to base64
            frame_b64 = base64.b64encode(buffer).decode('utf-8')
            frames.append(f"data:image/jpeg;base64,{frame_b64}")
        
        # Send request
        print("   Sending frames to API...")
        response = requests.post(
            f"{API_URL}/api/sign/recognize",
            json={"frames": frames, "return_sentence": True},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Sign recognition PASSED")
                print(f"   Sign: {data.get('sign')}")
                print(f"   Confidence: {data.get('confidence', 0):.2f}")
                print(f"   Frames processed: {data.get('frames_processed')}")
                print(f"   Valid frames: {data.get('valid_frames')}")
            else:
                print("⚠️  Sign recognition returned success=false")
                print(f"   Error: {data.get('error')}")
            return True
        else:
            print(f"❌ Sign recognition FAILED: Status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Sign recognition test error: {e}")
        return False


def test_biometric_list():
    """Test list enrolled users endpoint"""
    print("\n" + "=" * 70)
    print("TEST 3: List Enrolled Users")
    print("=" * 70)
    
    try:
        response = requests.get(f"{API_URL}/api/biometric/users", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            users = data.get('users', [])
            print("✅ List users PASSED")
            print(f"   Total enrolled: {data.get('total', 0)}")
            
            if users:
                print("   Users:")
                for user in users[:5]:  # Show first 5
                    print(f"      - {user.get('user_id')} (auth count: {user.get('authentication_count')})")
            else:
                print("   No users enrolled yet")
            return True
        else:
            print(f"❌ List users FAILED: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ List users test error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("NS-AGF API Service Test Suite")
    print("=" * 70)
    print(f"Testing API at: {API_URL}")
    
    results = []
    
    # Test 1: Health check
    results.append(("Health Check", test_health()))
    
    # Test 2: Sign recognition (only if health check passed)
    if results[0][1]:
        results.append(("Sign Recognition", test_sign_recognition()))
        results.append(("List Users", test_biometric_list()))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<50} {status}")
    
    print("-" * 70)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests PASSED! API service is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the output above.")
    
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
