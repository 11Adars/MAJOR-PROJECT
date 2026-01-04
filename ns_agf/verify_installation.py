"""
NS-AGF Installation Verification Script
========================================

Run this script to verify all components are properly installed
and can be imported without errors.

Usage:
    python verify_installation.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test all critical imports"""
    print("🔍 Testing NS-AGF component imports...\n")
    
    errors = []
    
    # Test 1: Graph topology
    print("1️⃣ Testing graph topology...")
    try:
        from src.graph import MediaPipeGraph
        graph = MediaPipeGraph()
        assert graph.num_nodes == 75
        print("   ✅ Graph topology: OK")
    except Exception as e:
        print(f"   ❌ Graph topology: FAILED")
        errors.append(f"Graph: {str(e)}")
    
    # Test 2: Model
    print("2️⃣ Testing model architecture...")
    try:
        from src.model import Model
        print("   ✅ Model import: OK")
    except Exception as e:
        print(f"   ❌ Model import: FAILED")
        errors.append(f"Model: {str(e)}")
    
    # Test 3: Verifier
    print("3️⃣ Testing neuro-symbolic verifier...")
    try:
        from src.logic import NeuroSymbolicVerifier, IntentType
        verifier = NeuroSymbolicVerifier()
        print("   ✅ Verifier: OK")
    except Exception as e:
        print(f"   ❌ Verifier: FAILED")
        errors.append(f"Verifier: {str(e)}")
    
    # Test 4: MediaPipe helper
    print("4️⃣ Testing MediaPipe helper...")
    try:
        from src.utils import MediaPipeExtractor, create_sequence_buffer
        print("   ✅ MediaPipe helper: OK")
    except Exception as e:
        print(f"   ❌ MediaPipe helper: FAILED")
        errors.append(f"MediaPipe: {str(e)}")
    
    # Test 5: Model loader
    print("5️⃣ Testing model loader...")
    try:
        from src.utils import fetch_trained_weights, verify_model
        print("   ✅ Model loader: OK")
    except Exception as e:
        print(f"   ❌ Model loader: FAILED")
        errors.append(f"Model loader: {str(e)}")
    
    return errors


def test_dependencies():
    """Test required dependencies"""
    print("\n🔍 Testing dependencies...\n")
    
    deps = {
        'torch': 'PyTorch',
        'cv2': 'OpenCV',
        'mediapipe': 'MediaPipe',
        'numpy': 'NumPy'
    }
    
    missing = []
    
    for module, name in deps.items():
        try:
            __import__(module)
            print(f"   ✅ {name}: Installed")
        except ImportError:
            print(f"   ❌ {name}: NOT INSTALLED")
            missing.append(name)
    
    return missing


def test_model_weights():
    """Check if model weights exist"""
    print("\n🔍 Checking model weights...\n")
    
    model_path = Path(__file__).parent / 'models' / 'ns_agcn.pth'
    
    if model_path.exists():
        print(f"   ✅ Model found: {model_path}")
        
        # Try to verify
        try:
            from src.utils import verify_model
            if verify_model(str(model_path)):
                print("   ✅ Model verified: Valid")
            else:
                print("   ⚠️ Model verification: Failed")
        except Exception as e:
            print(f"   ⚠️ Could not verify model: {e}")
    else:
        print(f"   ⚠️ Model not found: {model_path}")
        print("   📥 You need to train on Kaggle first!")
        print("   📖 See: kaggle_scripts/README_KAGGLE.md")


def main():
    """Run all tests"""
    print("=" * 60)
    print("NS-AGF Installation Verification")
    print("=" * 60)
    print()
    
    # Test imports
    import_errors = test_imports()
    
    # Test dependencies
    missing_deps = test_dependencies()
    
    # Test model
    test_model_weights()
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    if not import_errors and not missing_deps:
        print("✅ All components verified successfully!")
        print("\n📝 Next steps:")
        print("   1. Train model on Kaggle (if not done)")
        print("   2. Run: python inference.py --camera 0")
        print("   3. See: IMPLEMENTATION_GUIDE.md")
    else:
        print("⚠️ Some issues detected:\n")
        
        if import_errors:
            print("Import Errors:")
            for error in import_errors:
                print(f"   - {error}")
        
        if missing_deps:
            print("\nMissing Dependencies:")
            for dep in missing_deps:
                print(f"   - {dep}")
            print("\n📦 Install with:")
            print("   pip install -r requirements_nsagf.txt")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
