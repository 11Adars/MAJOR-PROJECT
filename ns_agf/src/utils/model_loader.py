"""
Model Loader - Download Trained Weights from Kaggle
====================================================

This module handles downloading pre-trained NS-AGF model weights from Kaggle.
"""

import os
import shutil
from pathlib import Path
from typing import Optional
import warnings


def fetch_trained_weights(
    kaggle_model_handle: Optional[str] = None,
    target_dir: str = "./ns_agf/models",
    force_download: bool = False
) -> str:
    """
    Download trained NS-AGF model weights from Kaggle.
    
    Args:
        kaggle_model_handle: Kaggle model identifier (e.g., 'username/model-name/framework/version')
                            If None, assumes manual download
        target_dir: Local directory to save model
        force_download: Force re-download even if model exists
    
    Returns:
        Path to the downloaded model file
    
    Raises:
        FileNotFoundError: If model not found locally and Kaggle download fails
        ImportError: If kagglehub not installed
    """
    # Create target directory
    os.makedirs(target_dir, exist_ok=True)
    
    model_path = os.path.join(target_dir, "ns_agcn.pth")
    
    # Check if model already exists locally
    if os.path.exists(model_path) and not force_download:
        print(f"✅ Model already exists at: {model_path}")
        print("   Use force_download=True to re-download")
        return model_path
    
    # Attempt Kaggle download
    if kaggle_model_handle:
        try:
            import kagglehub
            
            print(f"⬇️ Downloading model from Kaggle: {kaggle_model_handle}")
            
            # Download model
            cache_path = kagglehub.model_download(kaggle_model_handle)
            print(f"✅ Model downloaded to cache: {cache_path}")
            
            # Find .pth file in cache
            pth_files = list(Path(cache_path).rglob("*.pth"))
            
            if not pth_files:
                raise FileNotFoundError(f"No .pth file found in {cache_path}")
            
            # Copy to target directory
            source_file = pth_files[0]
            shutil.copy(source_file, model_path)
            
            print(f"✅ Model installed to: {model_path}")
            return model_path
            
        except ImportError:
            print("⚠️ kagglehub not installed. Install with: pip install kagglehub")
            print("   Falling back to manual download instructions...")
        
        except Exception as e:
            print(f"⚠️ Kaggle download failed: {e}")
            print("   Falling back to manual download instructions...")
    
    # Manual download instructions
    print("\n" + "=" * 60)
    print("📥 MANUAL DOWNLOAD REQUIRED")
    print("=" * 60)
    print("\nPlease download the model manually:")
    print("\n1. Go to your Kaggle notebook where you trained the model")
    print("2. Navigate to the 'Output' tab")
    print("3. Find 'ns_agcn_bankassist.pth'")
    print("4. Download the file")
    print(f"5. Place it at: {os.path.abspath(model_path)}")
    print("\nOR")
    print("\n1. If you created a Kaggle Model:")
    print("2. Install kagglehub: pip install kagglehub")
    print("3. Authenticate: kaggle login (or set KAGGLE_USERNAME/KAGGLE_KEY)")
    print("4. Call this function with your model handle:")
    print("   fetch_trained_weights('your-username/your-model-name/pytorch/1')")
    print("=" * 60)
    
    raise FileNotFoundError(
        f"Model not found at {model_path}. Please download manually (see instructions above)."
    )


def verify_model(model_path: str) -> bool:
    """
    Verify that the model file is valid.
    
    Args:
        model_path: Path to model file
    
    Returns:
        True if valid, False otherwise
    """
    if not os.path.exists(model_path):
        print(f"❌ Model file not found: {model_path}")
        return False
    
    try:
        import torch
        
        # Try loading (PyTorch 2.6 compatibility fix)
        state_dict = torch.load(model_path, map_location='cpu', weights_only=False)
        
        # Check basic structure
        if not isinstance(state_dict, dict):
            print("❌ Model file is not a valid state dictionary")
            return False
        
        print(f"✅ Model verified: {len(state_dict)} parameter tensors")
        return True
        
    except Exception as e:
        print(f"❌ Model verification failed: {e}")
        return False


def load_model_with_weights(
    model_class,
    weights_path: str,
    num_classes: int = 100,
    device: str = 'cpu'
):
    """
    Load model architecture and weights.
    
    Args:
        model_class: Model class (from ns_agf.src.model.agcn)
        weights_path: Path to weights file
        num_classes: Number of output classes
        device: Device to load model on
    
    Returns:
        Loaded model ready for inference
    """
    import torch
    
    # Initialize model
    model = model_class(
        num_class=num_classes,
        num_point=75,
        num_person=1,
        graph_args={'labeling_mode': 'spatial'},
        in_channels=3
    )
    
    # Load weights
    if not os.path.exists(weights_path):
        raise FileNotFoundError(f"Weights not found at {weights_path}")
    
    state_dict = torch.load(weights_path, map_location=device)
    model.load_state_dict(state_dict)
    
    # Set to evaluation mode
    model.eval()
    model = model.to(device)
    
    print(f"✅ Model loaded successfully")
    print(f"   Weights: {weights_path}")
    print(f"   Device: {device}")
    print(f"   Classes: {num_classes}")
    
    return model


def check_kaggle_auth() -> bool:
    """
    Check if Kaggle authentication is configured.
    
    Returns:
        True if authenticated, False otherwise
    """
    import os
    
    # Check for environment variables
    has_env = 'KAGGLE_USERNAME' in os.environ and 'KAGGLE_KEY' in os.environ
    
    # Check for kaggle.json
    kaggle_json = Path.home() / '.kaggle' / 'kaggle.json'
    has_json = kaggle_json.exists()
    
    if has_env or has_json:
        print("✅ Kaggle authentication configured")
        return True
    else:
        print("⚠️ Kaggle authentication not found")
        print("   Set KAGGLE_USERNAME and KAGGLE_KEY environment variables")
        print("   OR place kaggle.json in ~/.kaggle/")
        return False


# ==================== TESTING ====================
if __name__ == "__main__":
    print("🔬 Testing Model Loader...")
    
    # Check Kaggle auth
    print("\n--- Checking Kaggle Authentication ---")
    check_kaggle_auth()
    
    # Test local model check
    print("\n--- Checking for Local Model ---")
    model_dir = "./ns_agf/models"
    model_path = os.path.join(model_dir, "ns_agcn.pth")
    
    if os.path.exists(model_path):
        print(f"✅ Model found: {model_path}")
        verify_model(model_path)
    else:
        print(f"⚠️ Model not found: {model_path}")
        print("   You need to train on Kaggle first!")
    
    print("\n📝 Usage Example:")
    print("""
from ns_agf.src.utils.model_loader import fetch_trained_weights, load_model_with_weights
from ns_agf.src.model.agcn import Model

# Download weights (if not present)
weights_path = fetch_trained_weights(
    kaggle_model_handle='your-username/ns-agcn-model/pytorch/1'
)

# Load model
model = load_model_with_weights(
    model_class=Model,
    weights_path=weights_path,
    num_classes=100,
    device='cpu'
)

# Use for inference
# See inference.py for complete example
    """)
    
    print("\n✨ Model loader ready!")
