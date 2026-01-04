"""Test script to debug enhanced biometric service"""
import sys
import traceback

try:
    print("🔍 Testing enhanced service import...")
    import biometric_fusion_service_enhanced
    print("✅ Import successful")
    
    print("\n🔍 Testing Flask app...")
    app = biometric_fusion_service_enhanced.app
    print(f"✅ Flask app: {app}")
    
    print("\n🔍 Testing authenticator...")
    auth = biometric_fusion_service_enhanced.authenticator
    print(f"✅ Authenticator mode: {auth.mode}")
    print(f"✅ Threshold: {auth.threshold}")
    print(f"✅ Weights: face={auth.face_weight}, hand={auth.hand_weight}, style={auth.style_weight}")
    
    print("\n✅ All tests passed! Service should start normally.")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)
