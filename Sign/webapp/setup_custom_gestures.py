"""
Setup script for custom gesture system
"""
import os
import subprocess
import sys

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'opencv-python',
        'mediapipe',
        'pandas',
        'numpy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} is missing")
    
    return missing_packages

def install_packages(packages):
    """Install missing packages"""
    if packages:
        print(f"\nInstalling missing packages: {packages}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)
            print("✓ All packages installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("✗ Failed to install packages")
            return False
    return True

def create_directories():
    """Create necessary directories"""
    directories = [
        "custom_gestures",
        "processed_data",
        "backup"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def backup_original_dict():
    """Backup the original gesture dictionary"""
    dict_file = "module/islr/dict_sign.csv"
    backup_file = "backup/dict_sign_original.csv"
    
    if os.path.exists(dict_file):
        import shutil
        shutil.copy2(dict_file, backup_file)
        print(f"✓ Backed up original dictionary to: {backup_file}")
    else:
        print(f"✗ Dictionary file not found: {dict_file}")

def test_camera():
    """Test if camera is working"""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            print("✓ Camera is working")
            return True
        else:
            print("✗ Camera not working")
            return False
    except Exception as e:
        print(f"✗ Camera test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("=== Custom Gesture System Setup ===\n")
    
    # Check dependencies
    print("1. Checking dependencies...")
    missing = check_dependencies()
    
    if missing:
        install_success = install_packages(missing)
        if not install_success:
            print("Setup failed. Please install missing packages manually.")
            return
    
    # Create directories
    print("\n2. Creating directories...")
    create_directories()
    
    # Backup original files
    print("\n3. Backing up original files...")
    backup_original_dict()
    
    # Test camera
    print("\n4. Testing camera...")
    camera_ok = test_camera()
    
    # Final status
    print("\n=== Setup Complete ===")
    if camera_ok:
        print("✓ System is ready!")
        print("\nNext steps:")
        print("1. Run: python custom_gesture_workflow.py")
        print("2. Follow the prompts to add your gestures")
        print("3. Train the model with new data")
    else:
        print("⚠ Camera issue detected. Please check your camera connection.")
        print("You can still use the system but gesture collection won't work.")

if __name__ == "__main__":
    main()
