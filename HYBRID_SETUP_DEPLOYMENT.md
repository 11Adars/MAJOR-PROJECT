# Hybrid Sign Language System - Setup & Deployment Guide

## Quick Start (5 minutes)

### Prerequisites
- Python 3.8+
- Node.js 14+
- PostgreSQL 12+
- 4GB RAM minimum (8GB recommended for SLM)

### Step 1: Install Python Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Install NS-AGF specific requirements
pip install -r ns_agf/api_requirements.txt
```

### Step 2: Initialize Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE banking_system;

# Run schema
\c banking_system
\i backend/database_schema_tickets.sql
\i backend/migrate_sign_language_columns.sql

# Verify tables
SELECT table_name FROM information_schema.tables WHERE table_schema='public';
```

### Step 3: Start Services (in separate terminals)

```bash
# Terminal 1: Backend (Node.js)
cd backend
npm install
npm start

# Terminal 2: NS-AGF API Service (Python)
cd ns_agf
python api_service.py

# Terminal 3: Frontend (React)
cd frontend
npm install
npm start
```

### Step 4: Test the System

```bash
# Test NS-AGF hybrid endpoint
python ns_agf/test_hybrid_approach.py
```

## Detailed Setup

### Database Schema Updates

The system requires new columns in the `support_tickets` table:

```sql
-- If you're creating fresh
psql -U postgres -d banking_system -f backend/database_schema_tickets.sql

-- If you have existing tables
psql -U postgres -d banking_system -f backend/migrate_sign_language_columns.sql
```

### Environment Configuration

Create `.env` files:

#### Backend `.env`
```bash
# backend/.env
PORT=5000
DATABASE_URL=postgresql://user:password@localhost:5432/banking_system
NS_AGF_API=http://127.0.0.1:5002
NODE_ENV=production
JWT_SECRET=your_secret_key
```

#### NS-AGF `.env`
```bash
# ns_agf/.env
FLASK_ENV=production
SLM_ENABLED=true
SLM_TIMEOUT=30000
GPU_ENABLED=false
```

### Model Files

Ensure these files are present:

```
ns_agf/
├── models/
│   ├── ns_agcn.pth              ✓ Sign recognition model
│   ├── sign_labels.txt           ✓ Sign labels
│   └── label_names.npy           ✓ Label names
├── src/logic/
│   └── intent_rules.json         ✓ Banking intent rules
└── Sign/slm_model_cache/
    ├── tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
    └── [other model files]
```

### Verify Installation

```bash
# Check Python environment
python -c "import torch, cv2, mediapipe, ctransformers; print('✓ All packages installed')"

# Check Node environment
node -v && npm -v

# Check PostgreSQL
psql -U postgres -c "SELECT version();"

# Test NS-AGF API
curl http://127.0.0.1:5002/api/health

# Test Backend API
curl http://localhost:5000/api/health
```

## Service Port Mapping

| Service | Port | Purpose | Environment |
|---------|------|---------|-------------|
| Frontend | 3000 | React UI | Browser |
| Backend | 5000 | Express API | Node.js |
| NS-AGF | 5002 | Sign recognition + Query generation | Python/Flask |
| InsightFace | 5001 | Face authentication | Python |
| Biometric | 5002 | Multimodal biometrics | Python |
| PostgreSQL | 5432 | Database | PostgreSQL |

## Deployment Checklist

### Pre-Deployment

- [ ] All dependencies installed
- [ ] Database created and migrated
- [ ] Model files present
- [ ] Environment variables configured
- [ ] Tests passing locally
- [ ] Code committed to git

### Deployment Steps

```bash
# 1. Build frontend
cd frontend
npm run build

# 2. Copy build to backend public folder
cp -r build ../backend/public

# 3. Start services
# Use process manager like PM2
pm2 start backend/index.js --name backend
pm2 start ns_agf/api_service.py --name ns_agf --interpreter python3

# 4. Verify services
pm2 status
pm2 logs

# 5. Run health checks
curl http://localhost:5000/api/health
curl http://127.0.0.1:5002/api/health
```

### Using Docker (Optional)

```dockerfile
# Dockerfile for backend
FROM node:16

WORKDIR /app
COPY backend .
RUN npm install

EXPOSE 5000
CMD ["npm", "start"]
```

```dockerfile
# Dockerfile for NS-AGF
FROM python:3.10

WORKDIR /app
COPY ns_agf .
RUN pip install -r api_requirements.txt

EXPOSE 5002
CMD ["python", "api_service.py"]
```

```bash
# Build and run
docker build -t banking-backend -f Dockerfile.backend .
docker build -t ns-agf-api -f Dockerfile.nsagf .

docker run -p 5000:5000 banking-backend
docker run -p 5002:5002 ns-agf-api
```

## Performance Tuning

### For Better Recognition Accuracy

1. **Increase SLM Context Length**
```python
# ns_agf/src/slm/query_generator.py
max_new_tokens=100  # Increase from 50
```

2. **Lower Confidence Threshold**
```python
confidence_threshold=0.6  # More lenient
```

3. **Enable GPU for SLM**
```python
gpu_layers=50  # Enable GPU acceleration
```

### For Faster Response Times

1. **Cache Models in Memory**
```python
# Load models once at startup, reuse
inference_system = SignLanguageInference(...)
query_generator = QueryGenerator(...)
```

2. **Use Fallback Queries for Speed**
```python
use_slm=False  # Skip SLM, use fallback
```

3. **Reduce Frame Processing**
```python
max_frames=30  # Process fewer frames
```

### For Lower Memory Usage

1. **Use Smaller SLM Model**
```python
model_size="Q3_K"  # Smaller quantization
```

2. **Disable GPU**
```python
gpu_layers=0  # Use CPU only
```

3. **Limit Concurrent Requests**
```python
# Use queue/worker pool
from multiprocessing import Pool
pool = Pool(processes=2)
```

## Monitoring & Logging

### Application Logs

```bash
# Backend logs
tail -f backend/logs/app.log

# NS-AGF logs
tail -f ns_agf/logs/api.log

# Database logs
tail -f /var/log/postgresql/postgresql.log
```

### Health Check API

```bash
# Quick health check
curl http://localhost:5000/api/health
curl http://127.0.0.1:5002/api/health

# Response format
{
  "status": "ok",
  "service": "NS-AGF API",
  "inference_ready": true,
  "biometric_ready": true,
  "enrolled_users": 5
}
```

### Metrics Collection

```python
# Add to query_generator.py for monitoring
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

start_time = time.time()
query = generator.generate_query(...)
elapsed = time.time() - start_time

logger.info(f"Query generated in {elapsed:.2f}s")
logger.info(f"Model: TinyLlama, Tokens: 50, Temperature: 0.3")
```

## Troubleshooting Common Issues

### Issue: "NS-AGF API not responding"
```bash
# Solution 1: Start the service
python ns_agf/api_service.py

# Solution 2: Check port
netstat -an | grep 5002

# Solution 3: Check logs
python ns_agf/api_service.py 2>&1 | head -50
```

### Issue: "SLM Model not found"
```bash
# Solution: Download model
cd Sign
python -c "
from ctransformers import AutoModelForCausalLM
AutoModelForCausalLM.from_pretrained(
    'TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF',
    model_file='tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf'
)
"
```

### Issue: "Database connection failed"
```bash
# Solution: Check PostgreSQL
psql -U postgres -d banking_system -c "SELECT 1"

# Verify connection string
echo $DATABASE_URL

# Re-run migrations
psql -U postgres -d banking_system -f backend/migrate_sign_language_columns.sql
```

### Issue: "Memory error in SLM"
```bash
# Solution: Reduce model complexity
# In query_generator.py
self.slm_model = AutoModelForCausalLM.from_pretrained(
    model_name,
    model_type="llama",
    gpu_layers=0,  # Use CPU instead
)
```

## Scaling Considerations

### Single Server Setup
- Works for ~50-100 concurrent users
- 4-8GB RAM
- Single NS-AGF instance
- Single PostgreSQL instance

### Multi-Server Setup

```
Load Balancer (nginx/HAProxy)
    ├─ Backend Server 1 (5000)
    ├─ Backend Server 2 (5000)
    └─ Backend Server 3 (5000)

NS-AGF Cluster
    ├─ NS-AGF-1 (5002)
    ├─ NS-AGF-2 (5002)
    └─ NS-AGF-3 (5002)

Shared Database (PostgreSQL)
    └─ Primary + Replicas
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ns-agf-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ns-agf-api
  template:
    metadata:
      labels:
        app: ns-agf-api
    spec:
      containers:
      - name: ns-agf-api
        image: ns-agf-api:latest
        ports:
        - containerPort: 5002
        resources:
          requests:
            memory: "2Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 5002
          initialDelaySeconds: 30
          periodSeconds: 10
```

## Maintenance

### Regular Tasks

```bash
# Daily: Check service health
curl http://localhost:5000/api/health
curl http://127.0.0.1:5002/api/health

# Weekly: Review logs
grep "ERROR\|WARN" backend/logs/*.log

# Monthly: Database maintenance
VACUUM ANALYZE support_tickets;

# Quarterly: Update dependencies
pip install --upgrade -r requirements.txt
npm update
```

### Backup & Recovery

```bash
# Backup database
pg_dump banking_system > backup_$(date +%Y%m%d).sql

# Restore from backup
psql banking_system < backup_20260115.sql

# Backup model files
tar -czf models_backup_$(date +%Y%m%d).tar.gz ns_agf/models/
```

## Support & Documentation

- **Main Documentation**: [HYBRID_SIGN_LANGUAGE_DOCUMENTATION.md](./HYBRID_SIGN_LANGUAGE_DOCUMENTATION.md)
- **NS-AGF Guide**: [ns_agf/README_NSAGF.md](./ns_agf/README_NSAGF.md)
- **API Documentation**: [INTEGRATION_SUMMARY.md](./INTEGRATION_SUMMARY.md)
- **Quick Reference**: [DEMO_QUICK_REFERENCE.md](./DEMO_QUICK_REFERENCE.md)

## Next Steps

1. ✅ Complete setup
2. ✅ Run test suite
3. ✅ Deploy to staging
4. ✅ User testing
5. ✅ Deploy to production
6. ✅ Monitor and optimize

---

**Last Updated**: January 2026
**Version**: 1.0.0
**Status**: Production Ready
