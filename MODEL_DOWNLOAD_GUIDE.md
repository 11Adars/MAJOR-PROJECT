# 📦 Model Download Reference

## Quick Model Download Guide

### 🎯 Three Models Required

| Model | Size | Purpose | Auto-Download? |
|-------|------|---------|----------------|
| **NS-AGF** | ~50MB | Sign language recognition | ✅ Yes (on first run) |
| **TinyLlama SLM** | ~600MB | Query generation from signs | ✅ Yes (on first use) |
| **SpeechBrain** | ~200MB | Voice/speaker verification | ✅ Yes (on first use) |

**Total**: ~1GB disk space needed

---

## 1️⃣ NS-AGF Sign Language Model

### Auto-Download (Recommended)
```bash
# Starts automatically when you run api_service.py
cd ns_agf
python api_service.py
# Model downloads from Kaggle on first run
```

### Manual Download
```bash
cd ns_agf
python -c "from src.utils.model_loader import fetch_trained_weights; fetch_trained_weights()"
```

### Expected Location
```
ns_agf/models/nsagf_wlasl100_best.pth
```

### Troubleshooting
- **Error: Kaggle credentials not found**
  - No action needed - model may already be included
  - Or check if `models/` folder exists with .pth file

---

## 2️⃣ TinyLlama SLM (Query Generator)

### Auto-Download (Recommended)
```bash
# Downloads automatically on first query generation
cd ns_agf
python api_service.py
# When you submit first sign language query, SLM downloads
```

### Manual Pre-Download
```bash
# Test download before running app
cd ns_agf
python -c "from src.slm.query_generator import QueryGenerator; qg = QueryGenerator(use_slm=True)"
```

### Alternative Manual Download
```bash
pip install huggingface-hub
python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF', filename='tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf')"
```

### Expected Location
```
Sign/slm_model_cache/
# OR
~/.cache/huggingface/hub/
```

### Download Details
- **Source**: HuggingFace (TheBloke)
- **Model**: TinyLlama-1.1B-Chat-v1.0
- **Format**: GGUF (quantized INT4)
- **Size**: ~600MB
- **Time**: 2-5 minutes (depends on internet)

### Troubleshooting
- **Error: Connection timeout**
  ```bash
  # Check internet connection
  # Try using VPN if HuggingFace blocked
  # Or disable SLM (uses fallback queries)
  ```

- **Error: Out of disk space**
  ```bash
  # Free up at least 1GB space
  # Or disable SLM in api_service.py:
  # query_generator = QueryGenerator(use_slm=False)
  ```

- **Disable SLM** (optional - uses rule-based fallback):
  ```python
  # In ns_agf/api_service.py, change line:
  query_generator = QueryGenerator(use_slm=False)
  ```

### SLM is Optional!
- ✅ System works without SLM
- ✅ Uses intelligent fallback queries
- ⚠️ SLM provides better natural language output

---

## 3️⃣ SpeechBrain Voice Models

### Auto-Download (Recommended)
```bash
# Downloads automatically when voice service starts
cd python_service
python app.py
# Models download from SpeechBrain on first run
```

### Expected Location
```
python_service/pretrained_models/speaker_verification/
python_service/pretrained_models/spkrec-ecapa-voxceleb/
```

### Download Details
- **Source**: SpeechBrain official
- **Models**: ECAPA-TDNN (speaker embeddings)
- **Size**: ~200MB
- **Time**: 1-2 minutes

### Troubleshooting
- **Error: Cannot download models**
  ```bash
  # Check internet connection
  # Models auto-retry on next startup
  ```

---

## ⚡ Quick Setup Commands

### Download All Models Before First Run
```bash
# 1. NS-AGF Model
cd ns_agf
python -c "from src.utils.model_loader import fetch_trained_weights; fetch_trained_weights()"

# 2. TinyLlama SLM
python -c "from src.slm.query_generator import QueryGenerator; qg = QueryGenerator(use_slm=True)"

# 3. SpeechBrain Models
cd ../python_service
python app.py &
# Let it run for 2 minutes to download, then stop

cd ..
```

### Verify All Models Downloaded
```bash
# Check NS-AGF
ls ns_agf/models/nsagf_wlasl100_best.pth

# Check SLM
ls Sign/slm_model_cache/

# Check SpeechBrain
ls python_service/pretrained_models/
```

---

## 🌐 Internet Requirements

### During Installation
- **Required**: Yes
- **Speed**: 10+ Mbps recommended
- **Data**: ~1GB download
- **Time**: 5-10 minutes total

### During Runtime
- **Required**: Only for database (Supabase) and email
- **Models**: Run offline after downloaded
- **Note**: No internet needed for sign recognition after setup

---

## 📂 Expected Folder Structure After Downloads

```
MAJOR-PROJECT/
├── ns_agf/
│   └── models/
│       └── nsagf_wlasl100_best.pth          # ~50MB ✅
│
├── Sign/
│   └── slm_model_cache/
│       └── tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf  # ~600MB ✅
│
└── python_service/
    └── pretrained_models/
        ├── speaker_verification/             # ~100MB ✅
        └── spkrec-ecapa-voxceleb/           # ~100MB ✅
```

**Alternative SLM location** (if using system cache):
```
C:\Users\YourName\.cache\huggingface\hub\
```

---

## ⚠️ Troubleshooting Matrix

| Issue | Model | Solution |
|-------|-------|----------|
| Connection timeout | TinyLlama | Use VPN or disable SLM |
| Disk space full | All | Free 1GB space |
| Kaggle auth error | NS-AGF | Model may be pre-included |
| Slow download | All | Check internet speed |
| Model not found | Any | Check expected locations |
| Import error | All | Verify requirements installed |

---

## 🚀 First Run Checklist

- [ ] Internet connection active (10+ Mbps)
- [ ] 1GB+ free disk space
- [ ] Python virtual environment activated
- [ ] All requirements installed (`pip install -r requirements_complete.txt`)
- [ ] Run each service once to trigger auto-downloads
- [ ] Wait for all models to download (5-10 minutes)
- [ ] Verify models in expected locations
- [ ] Test sign recognition, voice auth, query generation

---

## 💡 Pro Tips

1. **Pre-download everything**: Run download commands before demo/presentation
2. **Use fast internet**: 10+ Mbps saves time
3. **SLM is optional**: Disable if download issues (fallback works great)
4. **Models cached**: Only downloads once, reused forever
5. **Offline capable**: After download, runs without internet (except DB/email)

---

## 📞 Need Help?

- Models not downloading? Check `PROJECT_SETUP_GUIDE.md` troubleshooting
- Internet issues? Try VPN or disable SLM temporarily  
- Disk space? Delete old logs, test videos, documentation files
- Still stuck? Check terminal output for specific error messages

---

**Last Updated**: January 9, 2026  
**Total Download Size**: ~1GB  
**Download Time**: 5-10 minutes  
**Models**: 3 (NS-AGF, TinyLlama, SpeechBrain)
