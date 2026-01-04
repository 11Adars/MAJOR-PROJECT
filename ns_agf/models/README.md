# Models Directory

This directory stores pre-trained NS-AGF model weights.

## 📥 How to Get Models

### Option 1: Download from Kaggle (Recommended)

After training your model on Kaggle:

```python
from ns_agf.src.utils.model_loader import fetch_trained_weights

# Download automatically
weights_path = fetch_trained_weights(
    kaggle_model_handle='your-username/ns-agcn-model/pytorch/1'
)
```

### Option 2: Manual Download

1. Go to your Kaggle notebook
2. Navigate to **Output** tab
3. Find `ns_agcn_bankassist.pth`
4. Download and place here as `ns_agcn.pth`

### Option 3: Train Locally (Not Recommended)

Local training is not supported due to computational requirements.
See `kaggle_scripts/README_KAGGLE.md` for Kaggle training instructions.

---

## 📂 Expected Files

- `ns_agcn.pth` - Main model weights (download from Kaggle)
- `.gitkeep` - Keep directory in git

**Note**: Model files are typically large (50-200MB) and should be added to `.gitignore`

---

## ✅ Verification

To verify your model is valid:

```python
from ns_agf.src.utils.model_loader import verify_model

is_valid = verify_model('./ns_agf/models/ns_agcn.pth')
```

---

## 🔒 Security Note

Do not commit large model files to git. Use:
- Git LFS for version control
- Kaggle Models for distribution
- Cloud storage (S3, Azure Blob) for deployment
