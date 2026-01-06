"""
Test script for Hybrid Sign Recognition + Query Generation
Tests the new /api/sign/hybrid-recognize endpoint

This script:
1. Tests sign recognition (AGCN)
2. Tests intent verification
3. Tests SLM query generation
4. Tests fallback queries if SLM unavailable
5. Provides timing information
"""

import requests
import json
import time
import base64
import cv2
import numpy as np
from pathlib import Path

# Configuration
API_BASE_URL = "http://127.0.0.1:5002"
TEST_VIDEO_PATH = "test.mp4"  # Use existing test video

# Colors for output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 70}")
    print(f"{text.center(70)}")
    print(f"{'=' * 70}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.ENDC}")

def print_section(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{text}{Colors.ENDC}")

def load_frames_from_video(video_path, max_frames=50):
    """Load frames from video file"""
    print_info(f"Loading frames from: {video_path}")
    
    if not Path(video_path).exists():
        print_error(f"Video file not found: {video_path}")
        return None
    
    cap = cv2.VideoCapture(video_path)
    frames = []
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frames.append(frame)
        frame_count += 1
        
        if frame_count >= max_frames:
            break
    
    cap.release()
    
    if frames:
        print_success(f"Loaded {len(frames)} frames from video")
    else:
        print_error("Failed to load frames")
    
    return frames

def encode_frames_to_base64(frames):
    """Encode OpenCV frames to base64 strings"""
    print_info("Encoding frames to base64...")
    
    encoded_frames = []
    for frame in frames:
        # Encode frame to JPEG bytes
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        
        # Encode to base64
        frame_b64 = base64.b64encode(frame_bytes).decode('utf-8')
        encoded_frames.append(frame_b64)
    
    print_success(f"Encoded {len(encoded_frames)} frames")
    return encoded_frames

def test_health_check():
    """Test API health check"""
    print_section("TEST 1: Health Check")
    
    try:
        start_time = time.time()
        response = requests.get(f"{API_BASE_URL}/api/health")
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"API is healthy (response time: {elapsed:.3f}s)")
            print(f"   Service: {data.get('service')}")
            print(f"   Version: {data.get('version')}")
            print(f"   Inference ready: {data.get('inference_ready')}")
            print(f"   Biometric ready: {data.get('biometric_ready')}")
            print(f"   Enrolled users: {data.get('enrolled_users')}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Health check error: {e}")
        return False

def test_standard_recognition(frames_b64):
    """Test standard sign recognition endpoint"""
    print_section("TEST 2: Standard Sign Recognition")
    
    try:
        payload = {
            "frames": frames_b64,
            "return_sentence": True
        }
        
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}/api/sign/recognize",
            json=payload
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Recognition successful (response time: {elapsed:.3f}s)")
            print(f"   Sign: {data.get('sign')}")
            print(f"   Confidence: {data.get('confidence'):.3f}")
            print(f"   Frames processed: {data.get('frames_processed')}")
            print(f"   Valid frames: {data.get('valid_frames')}")
            
            if 'intent' in data:
                intent = data.get('intent')
                print(f"   Banking intent: {intent.get('is_banking')}")
                print(f"   Intent type: {intent.get('intent_type')}")
            
            return data
        else:
            print_error(f"Recognition failed: {response.status_code}")
            if response.text:
                print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print_error(f"Recognition error: {e}")
        return False

def test_hybrid_recognition(frames_b64, use_slm=True):
    """Test hybrid sign recognition + query generation"""
    print_section("TEST 3: Hybrid Sign Recognition + Query Generation")
    
    try:
        payload = {
            "frames": frames_b64,
            "use_slm": use_slm
        }
        
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}/api/sign/hybrid-recognize",
            json=payload
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Hybrid recognition successful (response time: {elapsed:.3f}s)")
            print(f"   Sign: {data.get('sign')}")
            print(f"   Confidence: {data.get('confidence'):.3f}")
            print(f"   Intent: {data.get('intent')}")
            print(f"   Is banking intent: {data.get('is_banking_intent')}")
            print(f"   Generated query: {data.get('query')}")
            print(f"   SLM used: {data.get('slm_used')}")
            print(f"   Frames processed: {data.get('frames_processed')}")
            print(f"   Valid frames: {data.get('valid_frames')}")
            
            return data
        else:
            print_error(f"Hybrid recognition failed: {response.status_code}")
            if response.text:
                print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print_error(f"Hybrid recognition error: {e}")
        return False

def test_hybrid_without_slm(frames_b64):
    """Test hybrid recognition with SLM disabled (fallback)"""
    print_section("TEST 4: Hybrid Recognition with Fallback Queries (SLM disabled)")
    
    try:
        payload = {
            "frames": frames_b64,
            "use_slm": False  # Disable SLM
        }
        
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}/api/sign/hybrid-recognize",
            json=payload
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Hybrid (fallback) successful (response time: {elapsed:.3f}s)")
            print(f"   Sign: {data.get('sign')}")
            print(f"   Intent: {data.get('intent')}")
            print(f"   Generated query: {data.get('query')}")
            print(f"   SLM used: {data.get('slm_used')}")
            
            return data
        else:
            print_error(f"Hybrid (fallback) failed: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Hybrid (fallback) error: {e}")
        return False

def compare_results(standard_result, hybrid_result_slm, hybrid_result_fallback):
    """Compare results from different endpoints"""
    print_section("COMPARISON: Standard vs Hybrid Approaches")
    
    print(f"\n{'Aspect':<30} {'Standard':<20} {'Hybrid+SLM':<20} {'Hybrid+Fallback':<20}")
    print("-" * 90)
    
    # Sign recognition
    sign_std = standard_result.get('sign') if standard_result else "N/A"
    sign_hyb_slm = hybrid_result_slm.get('sign') if hybrid_result_slm else "N/A"
    sign_hyb_fb = hybrid_result_fallback.get('sign') if hybrid_result_fallback else "N/A"
    print(f"{'Recognized Sign':<30} {sign_std:<20} {sign_hyb_slm:<20} {sign_hyb_fb:<20}")
    
    # Confidence
    conf_std = f"{standard_result.get('confidence', 0):.3f}" if standard_result else "N/A"
    conf_hyb_slm = f"{hybrid_result_slm.get('confidence', 0):.3f}" if hybrid_result_slm else "N/A"
    conf_hyb_fb = f"{hybrid_result_fallback.get('confidence', 0):.3f}" if hybrid_result_fallback else "N/A"
    print(f"{'Confidence':<30} {conf_std:<20} {conf_hyb_slm:<20} {conf_hyb_fb:<20}")
    
    # Intent
    intent_std = "N/A"
    intent_hyb_slm = hybrid_result_slm.get('intent') if hybrid_result_slm else "N/A"
    intent_hyb_fb = hybrid_result_fallback.get('intent') if hybrid_result_fallback else "N/A"
    if standard_result and 'intent' in standard_result:
        intent_std = standard_result['intent'].get('intent_type', 'N/A')
    print(f"{'Intent':<30} {intent_std:<20} {intent_hyb_slm:<20} {intent_hyb_fb:<20}")
    
    # Query
    query_std = "N/A"
    query_hyb_slm = (hybrid_result_slm.get('query') if hybrid_result_slm else "N/A")[:30]
    query_hyb_fb = (hybrid_result_fallback.get('query') if hybrid_result_fallback else "N/A")[:30]
    if query_hyb_slm != "N/A":
        query_hyb_slm = query_hyb_slm + ("..." if len(hybrid_result_slm.get('query', '')) > 30 else "")
    if query_hyb_fb != "N/A":
        query_hyb_fb = query_hyb_fb + ("..." if len(hybrid_result_fallback.get('query', '')) > 30 else "")
    print(f"{'Generated Query':<30} {query_std:<20} {query_hyb_slm:<20} {query_hyb_fb:<20}")
    
    # SLM Status
    slm_std = "N/A"
    slm_hyb_slm = "Yes" if hybrid_result_slm and hybrid_result_slm.get('slm_used') else "Fallback"
    slm_hyb_fb = "Fallback"
    print(f"{'SLM Used':<30} {slm_std:<20} {slm_hyb_slm:<20} {slm_hyb_fb:<20}")

def main():
    """Main test routine"""
    print_header("HYBRID SIGN RECOGNITION + QUERY GENERATION TEST")
    
    print_info("This test verifies the hybrid approach combining:")
    print_info("  1. Sign recognition (AGCN)")
    print_info("  2. Intent verification")
    print_info("  3. Query generation (SLM)")
    print_info("  4. Fallback queries")
    
    # Test 1: Health check
    if not test_health_check():
        print_error("\nAPI is not responding. Make sure to start it with:")
        print_info("  python api_service.py")
        return False
    
    # Load test video
    if not Path(TEST_VIDEO_PATH).exists():
        print_warning(f"Test video not found: {TEST_VIDEO_PATH}")
        print_info("Creating synthetic frames for testing...")
        
        # Create synthetic frames (for testing without video)
        frames = []
        for i in range(30):
            frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
            frames.append(frame)
    else:
        frames = load_frames_from_video(TEST_VIDEO_PATH)
        if not frames:
            return False
    
    # Encode frames
    frames_b64 = encode_frames_to_base64(frames)
    
    # Test 2: Standard recognition
    standard_result = test_standard_recognition(frames_b64)
    
    # Test 3: Hybrid recognition with SLM
    hybrid_result_slm = test_hybrid_recognition(frames_b64, use_slm=True)
    
    # Test 4: Hybrid recognition with fallback
    hybrid_result_fallback = test_hybrid_recognition(frames_b64, use_slm=False)
    
    # Comparison
    if standard_result and hybrid_result_slm and hybrid_result_fallback:
        compare_results(standard_result, hybrid_result_slm, hybrid_result_fallback)
    
    # Summary
    print_header("TEST SUMMARY")
    
    results = {
        "Health Check": "✅ PASS",
        "Standard Recognition": "✅ PASS" if standard_result else "❌ FAIL",
        "Hybrid+SLM": "✅ PASS" if hybrid_result_slm else "❌ FAIL",
        "Hybrid+Fallback": "✅ PASS" if hybrid_result_fallback else "❌ FAIL"
    }
    
    for test_name, status in results.items():
        print(f"{test_name:<25} {status}")
    
    total_tests = len(results)
    passed_tests = sum(1 for status in results.values() if "PASS" in status)
    
    print(f"\n{'Total':<25} {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print_success("All tests passed! ✨")
    else:
        print_warning(f"{total_tests - passed_tests} test(s) failed")
    
    print("\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted")
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
