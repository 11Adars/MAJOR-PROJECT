# Step 3: Database Schema Update - Instructions

## 📋 What You Need to Do

Copy and run the SQL from [`database_schema_biometric.sql`](database_schema_biometric.sql) in your **Supabase SQL Editor**.

---

## 🚀 How to Run in Supabase

### Method 1: SQL Editor (Recommended)

1. **Go to your Supabase dashboard**
   - URL: https://supabase.com/dashboard/project/YOUR_PROJECT_ID

2. **Open SQL Editor**
   - Click "SQL Editor" in the left sidebar
   - Click "New query"

3. **Copy the entire SQL file**
   - Open [`backend/database_schema_biometric.sql`](backend/database_schema_biometric.sql)
   - Copy all contents (Ctrl+A, Ctrl+C)

4. **Paste and Run**
   - Paste into Supabase SQL Editor
   - Click "Run" button (or press Ctrl+Enter)

5. **Wait for completion**
   - Should take 2-3 seconds
   - You'll see success messages

---

## ✅ What This SQL Does

### 1. **Adds 4 Columns to `users` Table**
```sql
face_biometric           TEXT      -- 512-dim face features (base64)
hand_biometric           TEXT      -- 128-dim hand features (base64)
style_biometric          TEXT      -- 64-dim style features (base64)
biometric_registered_at  TIMESTAMP -- When enrolled
```

### 2. **Creates `biometric_auth_log` Table**
```sql
id                  SERIAL PRIMARY KEY
user_id             INTEGER (FK to users)
auth_timestamp      TIMESTAMP
auth_type           VARCHAR(50)  -- 'transfer', 'login', etc.
face_score          REAL         -- 0.0 to 1.0
hand_score          REAL
style_score         REAL
fusion_score        REAL         -- Overall score
authenticated       BOOLEAN      -- true if score >= 0.65
transaction_id      INTEGER (FK to transactions, optional)
ip_address          VARCHAR(45)
user_agent          TEXT
```

### 3. **Creates 5 Performance Indexes**
- `idx_biometric_auth_log_user_id` - Fast user lookups
- `idx_biometric_auth_log_timestamp` - Fast time-based queries
- `idx_biometric_auth_log_failed` - Security monitoring
- `idx_biometric_auth_log_type` - Auth type filtering
- `idx_biometric_auth_log_user_transaction` - Transaction linking

### 4. **Creates 3 Helper Functions**
- `user_has_biometrics(user_id)` - Check if enrolled
- `get_user_auth_stats(user_id)` - Get auth statistics
- `detect_suspicious_auth_activity(user_id)` - Security alerts

### 5. **Creates 1 View**
- `user_biometric_status` - Summary of all users' biometric status

---

## 🧪 Verification

After running the SQL, run these queries to verify:

### Check if columns were added:
```sql
SELECT 
    column_name, 
    data_type 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('face_biometric', 'hand_biometric', 'style_biometric', 'biometric_registered_at');
```

**Expected result:** 4 rows showing the new columns

---

### Check if table was created:
```sql
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_name = 'biometric_auth_log'
) as table_exists;
```

**Expected result:** `true`

---

### View all users' biometric status:
```sql
SELECT * FROM user_biometric_status;
```

**Expected result:** List of all users with `has_biometrics = false` (no one enrolled yet)

---

## 📊 Useful Queries After Setup

### See which users have enrolled biometrics:
```sql
SELECT 
    id, 
    username, 
    email,
    biometric_registered_at,
    CASE 
        WHEN face_biometric IS NOT NULL THEN 'Enrolled' 
        ELSE 'Not Enrolled' 
    END as status
FROM users
ORDER BY biometric_registered_at DESC NULLS LAST;
```

---

### View recent authentication attempts:
```sql
SELECT 
    u.username,
    bal.auth_type,
    bal.fusion_score,
    bal.authenticated,
    bal.auth_timestamp
FROM biometric_auth_log bal
JOIN users u ON bal.user_id = u.id
ORDER BY bal.auth_timestamp DESC
LIMIT 20;
```

---

### Get stats for a specific user (replace 1 with user ID):
```sql
SELECT * FROM get_user_auth_stats(1);
```

---

## ⚠️ Important Notes

### Data Types:
- **TEXT columns** store base64-encoded pickled numpy arrays
- **REAL columns** store floating-point scores (0.0 to 1.0)
- **TIMESTAMP columns** use PostgreSQL's default timezone

### Storage Size:
- Face biometric: ~1 KB per user
- Hand biometric: ~300 bytes per user
- Style biometric: ~200 bytes per user
- **Total per user: ~1.5 KB** (very small!)

### Performance:
- All indexes are optimized for common queries
- Auth log table can handle millions of records
- Indexes make queries fast even with large datasets

---

## 🔄 Rollback (If Needed)

If you want to undo these changes (NOT RECOMMENDED after data is added):

```sql
-- Drop everything (CAREFUL!)
DROP VIEW IF EXISTS user_biometric_status;
DROP FUNCTION IF EXISTS user_has_biometrics(INTEGER);
DROP FUNCTION IF EXISTS get_user_auth_stats(INTEGER);
DROP FUNCTION IF EXISTS detect_suspicious_auth_activity(INTEGER, INTEGER, INTEGER);
DROP TABLE IF EXISTS biometric_auth_log;
ALTER TABLE users DROP COLUMN IF EXISTS face_biometric;
ALTER TABLE users DROP COLUMN IF EXISTS hand_biometric;
ALTER TABLE users DROP COLUMN IF EXISTS style_biometric;
ALTER TABLE users DROP COLUMN IF EXISTS biometric_registered_at;
```

---

## ✅ After Running the SQL

Once you've run the SQL successfully, you can:

1. ✅ Verify the changes with the verification queries
2. ✅ Tell me "step 3 done" and we'll move to Step 4
3. ✅ Step 4 will add the backend endpoints to use these new tables

---

## 🆘 Troubleshooting

### Error: "relation 'users' does not exist"
**Solution:** Make sure you're running this on the correct database. Check your DATABASE_URL in `.env`.

### Error: "column 'face_biometric' already exists"
**Solution:** The columns already exist. This is fine - the SQL uses `IF NOT EXISTS` so it won't break.

### Error: "function already exists"
**Solution:** The SQL uses `CREATE OR REPLACE` so this shouldn't happen, but if it does, it's safe to ignore.

### Timeout error
**Solution:** The SQL should run in 2-3 seconds. If it times out, try running it in smaller chunks:
1. First run: STEP 1 only (ALTER TABLE commands)
2. Second run: STEP 2 only (CREATE TABLE command)
3. Third run: STEPs 3-5 (indexes, functions, view)

---

## 📈 Progress

**Step 3 Ready to Execute!**

✅ Step 1: NS-AGF API Service  
✅ Step 2: Backend Biometric Service  
🔄 Step 3: Database Schema ← **YOU ARE HERE** (SQL ready, waiting for you to run it)  
⏳ Step 4: Enrollment endpoint  
⏳ Step 5: Secure transfer endpoint  
⏳ Steps 6-9: Frontend + testing  

---

**Next**: After you run the SQL in Supabase, tell me **"step 3 done"** and I'll create the enrollment endpoint! 🚀
