# MAJOR-PROJECT
note:--------------------------------

## Project Setup

### Prerequisites
- Git LFS installed (`winget install GitHub.GitLFS`)
- Python 3.8 or higher
- Node.js 14 or higher

### Installation
1. Clone with Git LFS:
```bash
git lfs install
git clone https://github.com/11Adars/MAJOR-PROJECT.git
```

2. Install dependencies:
```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

-----------------------------------------------------------
table:

-- 1. Store user PINs (hashed)
CREATE TABLE user_pins (
  user_id INTEGER PRIMARY KEY REFERENCES users(id),
  pin_hash VARCHAR(255) NOT NULL
);

-- 2. Store user accounts (simulate one account per user)
CREATE TABLE accounts (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  account_number VARCHAR(20) UNIQUE NOT NULL,
  balance NUMERIC(12,2) DEFAULT 0
);

-- 3. Store beneficiaries for quick transfer
CREATE TABLE beneficiaries (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  name VARCHAR(100) NOT NULL,
  account_number VARCHAR(20) NOT NULL,
  ifsc VARCHAR(11) NOT NULL
);

-- 4. Store transaction history
CREATE TABLE transactions (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  type VARCHAR(10), -- 'credit' or 'debit'
  amount NUMERIC(12,2),
  to_account VARCHAR(20),
  status VARCHAR(20), -- 'success', 'failed', etc.
  reference_id VARCHAR(50), -- Razorpay payout/payment ID
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

5.



---------------------
npm install razorpay
npm install bcrypt

npm install react-router-dom axios react-icons
---------------------




.env::


# PostgreSQL Connection (adjust the username, password, db name as per your local setup)
DATABASE_URL=postgresql://postgres:Adarsh@123@db.lmaihyvwjbthawalhovn.supabase.co:5432/postgres

# Secret used for generating JWT tokens (change this to a strong random value)
JWT_SECRET=KqcJPyJChK5P/pviM65v8rAIOYdQ02tfOin0NQ6IWpmf4dKBCCL+drpJQzQvfeQfTjDsei8WfGitz85D72zILg==

# Python face embedding microservice URL (should match your Python server URL/port)
PYTHON_SERVICE_URL=http://127.0.0.1:5001/embed

PORT=5000


# ...existing env variables...
EMAIL_USER=adarsh.ds22@sahyadri.edu.in
EMAIL_APP_PASSWORD=gujtzvpdgaqiboaq


#razorpay
RAZORPAY_KEY_ID=rzp_test_vpCwG1s5IJZOwG
RAZORPAY_KEY_SECRET=7iVbBYTvG7prvvTerDG2AGuK

RAZORPAY_WEBHOOK_SECRET=adarshapoojary123****

## Gemini Sentence Generation (Optional)

Add natural language sentence generation for recognized ASL sign sequences.

1. Obtain a Gemini API key from Google AI Studio.
2. In `Sign-Language-Recognition-main/webapp/.env` add:
  ```
  GOOGLE_API_KEY=YOUR_GEMINI_KEY
  ENABLE_SENTENCE_GEN=true
  ```
3. Start the ISLR FastAPI server from the `webapp` directory:
  ```powershell
  uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
  ```
4. When multiple distinct signs are detected, the backend will call Gemini (debounced by unique sign sequence) to produce a coherent sentence. If unavailable, it falls back to a simple space-joined list.

Security:
- Do NOT commit real `.env` files.
- Rotate exposed keys.
- Keep placeholders only in any distributed `.env.example`.

