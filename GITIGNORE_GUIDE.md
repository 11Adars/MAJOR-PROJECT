# 🔒 .gitignore Reference Guide

## What Gets Ignored (Not Committed to Git)

### ⚠️ CRITICAL - Never Commit These:

1. **Environment Files** (.env)
   - Contains sensitive credentials (database passwords, API keys, email passwords)
   - Location: `backend/.env`
   - Use `.env.template` instead for sharing configuration structure

2. **Biometric Data** (.pkl, .db)
   - Contains user face/hand/voice biometric profiles
   - Security risk if exposed
   - Files: `biometric_data_enhanced.pkl`, `biometric_users.db`

3. **Uploaded User Files**
   - `backend/uploads/` - User photos, audio recordings
   - May contain personal/sensitive information

### 📦 Auto-Generated During Installation:

1. **Python Virtual Environment**
   - `venv/`, `.venv/`, `env/` - Ignored (can be recreated)
   - Recreate with: `python -m venv venv`

2. **Python Cache**
   - `__pycache__/`, `*.pyc`, `*.pyo` - Ignored (auto-regenerates)
   - Python bytecode files

3. **Node Modules**
   - `node_modules/` - Ignored (huge ~500MB)
   - Reinstall with: `npm install`
   - `package-lock.json` - Ignored (can cause conflicts)

4. **Build Outputs**
   - `frontend/build/` - React production build
   - `backend/dist/` - Compiled backend
   - Regenerate with: `npm run build`

### 🤖 Auto-Downloaded Models:

1. **NS-AGF Model** (~50MB)
   - `ns_agf/models/*.pth` - Ignored
   - Auto-downloads on first run
   - Download: `python -c "from src.utils.model_loader import fetch_trained_weights; fetch_trained_weights()"`

2. **TinyLlama SLM** (~600MB)
   - `Sign/slm_model_cache/*.gguf` - Ignored
   - Auto-downloads from HuggingFace on first query
   - Cache: `~/.cache/huggingface/`

3. **SpeechBrain Models** (~200MB)
   - `python_service/pretrained_models/` - Ignored
   - Auto-downloads on first voice service start

4. **InsightFace Models**
   - `~/.insightface/` - Ignored
   - Auto-downloads when biometric service starts

### 📊 Large Data Files:

1. **Video Files**
   - `*.mp4`, `*.avi`, `*.mov` - Ignored
   - Test videos excluded (too large for Git)
   - Use Git LFS if needed

2. **Processed Features**
   - `*.npy`, `*.npz` - Numpy arrays ignored
   - `gesture_data/*.csv` - Landmark data
   - Regenerate by preprocessing dataset

3. **Model Weights**
   - `*.h5`, `*.weights` - Keras/TensorFlow weights
   - `*.pkl`, `*.joblib` - Scikit-learn models

### 📝 Log Files:

- `*.log` - All log files ignored
- `backend/backend_error.log`
- `backend/backend_output.log`
- `api_out.log`

### 🛠️ IDE & Editor Files:

- `.vscode/` - VS Code settings (personal preferences)
- `.idea/` - PyCharm/IntelliJ settings
- `*.swp`, `*.swo` - Vim swap files

### 💻 OS Generated:

- `.DS_Store` - macOS folder metadata
- `Thumbs.db` - Windows thumbnail cache
- `desktop.ini` - Windows folder settings

---

## ✅ What DOES Get Committed:

### Source Code
- ✅ `backend/` - Node.js backend code
- ✅ `frontend/src/` - React frontend code
- ✅ `python_service/app.py` - Voice service code
- ✅ `ns_agf/` - Sign language service code (except models)
- ✅ `biometric_fusion_service_enhanced.py`

### Configuration Templates
- ✅ `.env.template` - Environment config template (NO SECRETS)
- ✅ `requirements_complete.txt` - Python dependencies
- ✅ `package.json` - Node.js dependencies

### Documentation
- ✅ `README*.md` - All markdown documentation
- ✅ `PROJECT_SETUP_GUIDE.md`
- ✅ `MODEL_DOWNLOAD_GUIDE.md`
- ✅ `QUICK_START.md`

### Database Schemas
- ✅ `backend/database_schema_biometric.sql`
- ✅ `backend/database_schema_tickets.sql`

### Scripts
- ✅ `start_all_services.bat` - Service starter
- ✅ `*.sh` - Shell scripts

### Placeholders
- ✅ `.gitkeep` files - Keep empty directories in Git

---

## 🔄 What to Recreate After Clone:

### 1. Python Setup (5 minutes)
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements_complete.txt
```

### 2. Node Setup (3 minutes)
```bash
cd backend && npm install && cd ..
cd frontend && npm install && cd ..
```

### 3. Environment Config (2 minutes)
```bash
copy .env.template backend\.env
# Edit backend/.env with your credentials
```

### 4. Database Setup (5 minutes)
- Create Supabase project
- Run SQL schemas
- Update DATABASE_URL in .env

### 5. Models Download (5-10 minutes - automatic)
- NS-AGF: Auto-downloads on first run
- TinyLlama: Auto-downloads on first query
- SpeechBrain: Auto-downloads on first voice service start
- Total: ~1GB download

---

## 🚨 Common Mistakes to Avoid:

### ❌ DON'T Commit:
1. `.env` file with real passwords
2. `node_modules/` folder (huge)
3. `venv/` folder (environment-specific)
4. Biometric data files (`.pkl`, `.db`)
5. User uploaded files (photos, audio)
6. Large model weights (`.pth`, `.gguf`)
7. Log files with sensitive info

### ✅ DO Commit:
1. Source code (`.py`, `.js`, `.jsx`)
2. Configuration templates (`.env.template`)
3. Documentation (`.md` files)
4. Database schemas (`.sql`)
5. Package configs (`package.json`, `requirements.txt`)
6. Scripts (`.bat`, `.sh`)

---

## 📦 Repository Size:

**After Proper .gitignore:**
- Source code + docs: ~10-20MB
- Total Git repo: ~20-30MB

**Without .gitignore (BAD):**
- With node_modules: ~500MB
- With models: ~1.5GB
- With user data: 2GB+
- ⚠️ Too large for Git!

---

## 🔍 Check What's Ignored:

```bash
# See all tracked files
git ls-files

# Check if specific file is ignored
git check-ignore -v backend/.env

# See what would be committed
git status

# See ignored files
git status --ignored
```

---

## 🛠️ Fix Accidentally Committed Files:

### If you committed .env:
```bash
# Remove from Git but keep locally
git rm --cached backend/.env
git commit -m "Remove .env from tracking"

# Immediately change all passwords in .env!
```

### If you committed node_modules:
```bash
git rm -r --cached node_modules/
git commit -m "Remove node_modules"
```

### If you committed models:
```bash
git rm --cached ns_agf/models/*.pth
git commit -m "Remove large model files"
```

---

## 📊 Before Pushing - Checklist:

- [ ] No `.env` files in commit
- [ ] No `node_modules/` in commit
- [ ] No `venv/` in commit
- [ ] No `.pkl` biometric data in commit
- [ ] No large model files (`.pth`, `.gguf`) in commit
- [ ] No user uploaded files in commit
- [ ] No log files with errors in commit
- [ ] Only source code, docs, configs committed

---

## 🔗 Related Files:

- `.gitignore` - This file's configuration
- `.env.template` - Safe config template to commit
- `.gitkeep` - Placeholder to keep empty directories

---

**Last Updated**: January 9, 2026  
**Purpose**: Prevent sensitive data, large files, and auto-generated files from being committed to Git  
**Status**: Comprehensive coverage for NS-AGF Banking System
