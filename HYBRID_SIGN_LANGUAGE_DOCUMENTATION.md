# Hybrid Sign Language Recognition + Query Generation

## Overview

The hybrid approach combines multiple components to provide a complete customer support experience for sign language users:

1. **Sign Recognition (AGCN)** - Fast, deterministic recognition of sign language gestures
2. **Intent Verification** - Banking-specific intent classification
3. **Query Generation (SLM)** - Natural language query generation using Small Language Models
4. **Fallback Mechanism** - Rule-based queries when SLM is unavailable

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                      │
│                   - Video recording UI                       │
│                   - Frame capture (30-50 fps)               │
└────────────────────┬────────────────────────────────────────┘
                     │ (base64 frames)
                     ↓
        ┌──────────────────────────────┐
        │  BACKEND (Express/Node.js)   │
        │  Port 5000                   │
        │ POST /api/support/tickets/   │
        │       hybrid-sign            │
        └──────────┬───────────────────┘
                   │
                   ↓
    ┌──────────────────────────────────┐
    │    NS-AGF API Service            │
    │    Port 5002                     │
    │ POST /api/sign/hybrid-recognize  │
    └──────────┬───────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
    ↓                     ↓
┌─────────────┐  ┌──────────────────┐
│   AGCN      │  │  Intent          │
│   Model     │  │  Verifier        │
│ ns_agcn.pth │  │  intent_rules.json
└─────────────┘  └──────────────────┘
    │                     │
    └──────────┬──────────┘
               ↓
    ┌──────────────────────────┐
    │  SLM Query Generator     │
    │  (TinyLlama/Phi-3)       │
    │ ctransformers + gguf     │
    └──────────┬───────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
    ↓                     ↓
┌─────────────────┐  ┌──────────────┐
│ Generated Query │  │   Fallback   │
│  (SLM Output)   │  │    Query     │
└─────────────────┘  └──────────────┘
    │                     │
    └──────────┬──────────┘
               ↓
    ┌──────────────────────────┐
    │   BACKEND continued      │
    │  - Store in database     │
    │  - Send emails           │
    │  - Return response       │
    └──────────┬───────────────┘
               │
               ↓
    ┌──────────────────────────┐
    │   DATABASE (PostgreSQL)  │
    │ support_tickets table    │
    │  - sign_recognized       │
    │  - intent_detected       │
    │  - generated_query       │
    │  - slm_used              │
    └──────────────────────────┘
```

## Components

### 1. NS-AGF (Port 5002)

Located in: `ns_agf/api_service.py`

#### New Endpoint: `POST /api/sign/hybrid-recognize`

**Request:**
```json
{
  "frames": [
    "base64_encoded_frame_1",
    "base64_encoded_frame_2",
    ...
  ],
  "use_slm": true
}
```

**Response:**
```json
{
  "success": true,
  "sign": "HELP",
  "confidence": 0.95,
  "intent": "customer_support",
  "is_banking_intent": true,
  "query": "I need help with banking services",
  "slm_used": true,
  "frames_processed": 50,
  "valid_frames": 48
}
```

#### Process Flow:

1. **Frame Decoding** - Convert base64 frames to OpenCV format
2. **Landmark Extraction** - Extract hand/pose landmarks using MediaPipe
3. **Sign Recognition** - Predict sign using NS-AGCN model
4. **Intent Verification** - Check if sign corresponds to banking intent
5. **Query Generation** - Generate natural language query using SLM or fallback

### 2. Query Generator (SLM)

Located in: `ns_agf/src/slm/query_generator.py`

#### Class: `QueryGenerator`

```python
from src.slm.query_generator import QueryGenerator

# Initialize
generator = QueryGenerator(
    use_slm=True,
    cache_path="../Sign/slm_model_cache"
)

# Generate query
query = generator.generate_query(
    sign_name="HELP",
    intent="customer_support",
    hand_landmarks=landmarks
)
```

#### Features:

- **TinyLlama Integration**: Uses `ctransformers` with GGUF quantized model
- **Fallback Queries**: Pre-defined queries when SLM unavailable
- **Few-shot Prompting**: Examples provided to the model for better results
- **Error Handling**: Graceful degradation if SLM fails

#### SLM Configuration:

```python
MODEL_NAME = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
MODEL_FILE = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
CACHE_PATH = "../Sign/slm_model_cache"
```

### 3. Backend Support Controller

Located in: `backend/controllers/supportController.js`

#### New Function: `submitHybridSignTicket`

**Route:** `POST /api/support/tickets/hybrid-sign`

**Process:**

1. **Validation** - Ensure minimum 10 frames provided
2. **NS-AGF Call** - Send frames to hybrid recognition endpoint
3. **Response Parsing** - Extract sign, intent, query from response
4. **Database Insert** - Store ticket with sign language metadata
5. **Email Notification** - Send to bank staff and user
6. **Response** - Return ticket details with recognition metadata

### 4. Database Schema

#### New Columns in `support_tickets`:

```sql
sign_recognized VARCHAR(255)      -- The sign that was recognized (e.g., "HELP")
intent_detected VARCHAR(100)      -- Banking intent (e.g., "customer_support")
slm_used BOOLEAN                  -- Whether SLM was used for query
confidence_score DECIMAL(3, 2)    -- Confidence in sign recognition (0.0-1.0)
```

#### Migration:

Run the migration script:
```bash
psql -U postgres -d your_db -f backend/migrate_sign_language_columns.sql
```

Or manually run:
```sql
ALTER TABLE support_tickets
ADD COLUMN IF NOT EXISTS sign_recognized VARCHAR(255),
ADD COLUMN IF NOT EXISTS intent_detected VARCHAR(100),
ADD COLUMN IF NOT EXISTS slm_used BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS confidence_score DECIMAL(3, 2);
```

## Implementation Details

### Query Generator Logic

#### Step 1: Keyword Extraction
```python
def _extract_keywords(sign_name, intent, hand_landmarks):
    keywords = [sign_name]
    
    # Add intent-specific keywords
    intent_keywords = {
        'customer_support': ['HELP', 'SUPPORT'],
        'send_money': ['TRANSFER', 'MONEY'],
        'check_balance': ['BALANCE', 'ACCOUNT'],
        ...
    }
    
    return keywords
```

#### Step 2: SLM Generation
```python
def _slm_generate_sentence(keywords):
    prompt = f"""
    <|system|>
    You are a helpful banking assistant.
    Convert keyword lists into a complete banking query sentence.
    </s>
    
    <|user|>
    Keywords: {', '.join(keywords)}</s>
    <|assistant|>
    """
    
    # Generate using TinyLlama
    return model(prompt, max_tokens=50)
```

#### Step 3: Fallback Query
```python
def _get_fallback_query(sign_name, intent):
    fallback_queries = {
        'customer_support': f"Customer signed '{sign_name}' and needs assistance",
        ...
    }
    return fallback_queries.get(intent, default)
```

### Intent Rules

Located in: `ns_agf/src/logic/intent_rules.json`

```json
{
  "HELP": {
    "intent": "customer_support",
    "category": "banking",
    "description": "Customer needs assistance with banking services"
  },
  "TRANSFER": {
    "intent": "send_money",
    "category": "banking",
    "description": "Customer wants to transfer money"
  },
  ...
}
```

## Usage

### From Frontend

```javascript
// Capture video frames and send to backend
const frames = captureFrames(video, 30, 50); // 30-50 frames

const response = await fetch('/api/support/tickets/hybrid-sign', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    frames: frames.map(f => f.toDataURL('image/jpeg')),
    use_slm: true
  })
});

const result = await response.json();
console.log('Recognized sign:', result.sign_language_data.sign_recognized);
console.log('Generated query:', result.sign_language_data.query_generated);
```

### From Backend

```javascript
const axios = require('axios');

const response = await axios.post('http://127.0.0.1:5002/api/sign/hybrid-recognize', {
  frames: base64Frames,
  use_slm: true
});

console.log(response.data.query);  // Natural language query
```

## Configuration

### Environment Variables

```bash
# .env file
NS_AGF_API=http://127.0.0.1:5002
SLM_ENABLED=true
SLM_TIMEOUT=30000  # milliseconds
```

### API Service Configuration

In `ns_agf/api_service.py`:

```python
# SLM Configuration
SLM_MODEL_NAME = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
SLM_CACHE_PATH = "../Sign/slm_model_cache"
SLM_GPU_LAYERS = 0  # Set to 50+ if you have GPU

# Recognition Configuration
CONFIDENCE_THRESHOLD = 0.7
VERIFICATION_THRESHOLD = 0.65
```

## Testing

### Run Tests

```bash
# Install dependencies
pip install -r ns_agf/api_requirements.txt

# Start NS-AGF API service
python ns_agf/api_service.py

# In another terminal, run tests
python ns_agf/test_hybrid_approach.py
```

### Test Coverage

1. **Health Check** - Verify API is running
2. **Standard Recognition** - Test sign recognition alone
3. **Hybrid+SLM** - Test with SLM query generation
4. **Hybrid+Fallback** - Test with fallback queries
5. **Comparison** - Compare results across approaches

### Example Test Output

```
======================================================================
                HYBRID SIGN RECOGNITION + QUERY GENERATION TEST
======================================================================

TEST 1: Health Check
✅ API is healthy (response time: 0.045s)
   Service: NS-AGF API
   Version: 1.0.0
   Inference ready: True
   Biometric ready: True
   Enrolled users: 0

TEST 2: Standard Sign Recognition
✅ Recognition successful (response time: 0.892s)
   Sign: HELP
   Confidence: 0.9487
   Frames processed: 50
   Valid frames: 48
   Banking intent: True
   Intent type: customer_support

TEST 3: Hybrid Sign Recognition + Query Generation
✅ Hybrid recognition successful (response time: 8.234s)
   Sign: HELP
   Confidence: 0.9487
   Intent: customer_support
   Is banking intent: True
   Generated query: I need help with banking services
   SLM used: True
   Frames processed: 50
   Valid frames: 48

TEST 4: Hybrid Recognition with Fallback Queries
✅ Hybrid (fallback) successful (response time: 1.123s)
   Sign: HELP
   Intent: customer_support
   Generated query: Customer signed 'HELP' and needs assistance with banking services
   SLM used: False
```

## Performance

### Timing Breakdown

| Component | Time | Notes |
|-----------|------|-------|
| Frame decoding | 0.1-0.2s | Base64 → OpenCV |
| Landmark extraction | 0.3-0.5s | MediaPipe processing |
| Sign recognition | 0.2-0.3s | NS-AGCN model inference |
| Intent verification | 0.05-0.1s | Rule-based matching |
| SLM query generation | 5-10s | TinyLlama model inference |
| **Total (with SLM)** | **6-12s** | Depends on frames and model |
| **Total (fallback)** | **0.8-1.2s** | Much faster |

### Optimization Tips

1. **GPU Support** - Enable GPU layers for SLM (50+ layers)
2. **Model Caching** - Cache loaded models in memory
3. **Async Processing** - Run SLM generation in background
4. **Batch Processing** - Process multiple users' requests together

## Fallback Strategies

### If SLM Unavailable
- Use pre-defined intent-based queries
- Provide structured format with sign name + intent
- Still send to bank staff for manual follow-up

### If Sign Not Recognized
- Return error to user with confidence scores
- Suggest re-recording
- Option to manually type query

### If Intent Not Detected
- Treat as general inquiry
- Use generic support query template
- Bank staff can reclassify manually

## Security Considerations

1. **Frame Privacy** - Frames are sent over HTTPS only
2. **Token Authentication** - All endpoints require valid JWT token
3. **Database Encryption** - Consider encrypting stored videos
4. **Rate Limiting** - Limit SLM requests per user per day
5. **Audit Logging** - Log all sign language recognitions

## Monitoring

### Metrics to Track

```javascript
// Log structure
{
  timestamp: "2026-01-15T10:30:00Z",
  user_id: 110,
  sign_recognized: "HELP",
  confidence: 0.95,
  intent_detected: "customer_support",
  slm_used: true,
  query_generated: "I need help with banking services",
  processing_time_ms: 8234,
  status: "success"
}
```

### Key Performance Indicators

- **Recognition Accuracy** - % of correct sign predictions
- **Intent Accuracy** - % of correct intent classifications
- **Query Quality** - Semantic similarity of generated vs expected queries
- **System Availability** - Uptime of NS-AGF service
- **Response Time** - Average time to process request

## Troubleshooting

### NS-AGF Service Not Responding

```bash
# Check if service is running
curl http://127.0.0.1:5002/api/health

# If not, start it
python ns_agf/api_service.py
```

### SLM Not Loading

```bash
# Check TinyLlama installation
python -c "from ctransformers import AutoModelForCausalLM; print('OK')"

# Check model cache
ls Sign/slm_model_cache/

# Download if missing
python -c "from ctransformers import AutoModelForCausalLM; AutoModelForCausalLM.from_pretrained(...)"
```

### Memory Issues

```bash
# If SLM causes memory errors:
# 1. Reduce max_tokens in query_generator.py
# 2. Disable GPU layers (set gpu_layers=0)
# 3. Use smaller model variant
```

### Database Connection Error

```bash
# Check PostgreSQL connection
psql -U postgres -d banking_system -c "SELECT COUNT(*) FROM support_tickets;"

# Run migration
psql -U postgres -d banking_system -f backend/migrate_sign_language_columns.sql
```

## Future Enhancements

1. **Multi-sign Sequences** - Recognize sequences of signs
2. **Confidence Thresholding** - Ask user to repeat if confidence low
3. **Custom Models** - Train SLM on domain-specific queries
4. **Real-time Processing** - Stream frames instead of batch
5. **Sentiment Analysis** - Detect emotional tone from signing speed
6. **Language Variants** - Support different sign languages (ASL, BSL, etc.)

## References

- [NS-AGF Documentation](../ns_agf/README_NSAGF.md)
- [TinyLlama Model](https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF)
- [ctransformers](https://github.com/marella/ctransformers)
- [MediaPipe](https://developers.google.com/mediapipe)

## Support

For issues or questions:
1. Check logs in `ns_agf/` and `backend/logs/`
2. Run diagnostic tests: `python ns_agf/test_hybrid_approach.py`
3. Review health check: `curl http://127.0.0.1:5002/api/health`
4. Check database schema: `python backend/check_schema.py`
