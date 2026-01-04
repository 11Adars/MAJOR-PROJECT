-- ============================================================================
-- Database Schema Update for Biometric Authentication
-- ============================================================================
--
-- This SQL script adds biometric authentication support to your existing
-- banking database. Run this in your PostgreSQL/Supabase SQL console.
--
-- What this does:
-- 1. Adds 3 biometric columns to users table (face, hand, style)
-- 2. Creates biometric_auth_log table for tracking authentication attempts
-- 3. Adds indexes for performance
-- 4. Includes rollback instructions
--
-- Author: Banking System Team
-- Date: January 2026
-- Database: PostgreSQL (Supabase)
--
-- ============================================================================

-- ============================================================================
-- STEP 1: Add Biometric Columns to Users Table
-- ============================================================================

-- Add face biometric data (512-dim embedding, base64 encoded pickle)
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS face_biometric TEXT;

-- Add hand biometric data (128-dim hand geometry features, base64 encoded pickle)
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS hand_biometric TEXT;

-- Add style biometric data (64-dim behavioral features, base64 encoded pickle)
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS style_biometric TEXT;

-- Add timestamp for when biometrics were registered
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS biometric_registered_at TIMESTAMP;

-- Add comment for documentation
COMMENT ON COLUMN users.face_biometric IS 'Face recognition features (512-dim ArcFace embedding, base64 pickle)';
COMMENT ON COLUMN users.hand_biometric IS 'Hand geometry features (128-dim, base64 pickle)';
COMMENT ON COLUMN users.style_biometric IS 'Signing style features (64-dim behavioral, base64 pickle)';
COMMENT ON COLUMN users.biometric_registered_at IS 'Timestamp when user enrolled biometrics';

-- ============================================================================
-- STEP 2: Create Biometric Authentication Log Table
-- ============================================================================

-- This table tracks all biometric authentication attempts for audit and security
CREATE TABLE IF NOT EXISTS biometric_auth_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    auth_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    auth_type VARCHAR(50) NOT NULL, -- 'transfer', 'login', 'enrollment', etc.
    
    -- Individual biometric scores (0.0 to 1.0)
    face_score REAL,
    hand_score REAL,
    style_score REAL,
    fusion_score REAL NOT NULL, -- Overall weighted score
    
    -- Authentication result
    authenticated BOOLEAN NOT NULL,
    
    -- Optional: link to transaction if auth was for transfer
    transaction_id INTEGER REFERENCES transactions(id) ON DELETE SET NULL,
    
    -- Additional metadata
    ip_address VARCHAR(45), -- IPv4 or IPv6
    user_agent TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add comments
COMMENT ON TABLE biometric_auth_log IS 'Audit log for all biometric authentication attempts';
COMMENT ON COLUMN biometric_auth_log.auth_type IS 'Type of operation: transfer, login, enrollment, etc.';
COMMENT ON COLUMN biometric_auth_log.fusion_score IS 'Weighted average of all biometric scores (threshold: 0.65)';
COMMENT ON COLUMN biometric_auth_log.authenticated IS 'Whether authentication passed (fusion_score >= 0.65)';

-- ============================================================================
-- STEP 3: Create Indexes for Performance
-- ============================================================================

-- Index for querying auth logs by user
CREATE INDEX IF NOT EXISTS idx_biometric_auth_log_user_id 
ON biometric_auth_log(user_id);

-- Index for querying auth logs by timestamp (for analytics)
CREATE INDEX IF NOT EXISTS idx_biometric_auth_log_timestamp 
ON biometric_auth_log(auth_timestamp DESC);

-- Index for finding failed authentication attempts (security monitoring)
CREATE INDEX IF NOT EXISTS idx_biometric_auth_log_failed 
ON biometric_auth_log(user_id, authenticated, auth_timestamp DESC) 
WHERE authenticated = false;

-- Index for querying by auth type
CREATE INDEX IF NOT EXISTS idx_biometric_auth_log_type 
ON biometric_auth_log(auth_type, auth_timestamp DESC);

-- Composite index for user + transaction lookups
CREATE INDEX IF NOT EXISTS idx_biometric_auth_log_user_transaction 
ON biometric_auth_log(user_id, transaction_id) 
WHERE transaction_id IS NOT NULL;

-- ============================================================================
-- STEP 4: Create Helper Functions (Optional but Recommended)
-- ============================================================================

-- Function to check if user has enrolled biometrics
CREATE OR REPLACE FUNCTION user_has_biometrics(p_user_id INTEGER)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM users 
        WHERE id = p_user_id 
        AND face_biometric IS NOT NULL 
        AND hand_biometric IS NOT NULL 
        AND style_biometric IS NOT NULL
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION user_has_biometrics IS 'Check if user has completed biometric enrollment';

-- Function to get user authentication statistics
CREATE OR REPLACE FUNCTION get_user_auth_stats(p_user_id INTEGER)
RETURNS TABLE(
    total_attempts BIGINT,
    successful_attempts BIGINT,
    failed_attempts BIGINT,
    success_rate NUMERIC,
    avg_fusion_score NUMERIC,
    last_auth_timestamp TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_attempts,
        COUNT(*) FILTER (WHERE authenticated = true)::BIGINT as successful_attempts,
        COUNT(*) FILTER (WHERE authenticated = false)::BIGINT as failed_attempts,
        CASE 
            WHEN COUNT(*) > 0 THEN 
                ROUND((COUNT(*) FILTER (WHERE authenticated = true)::NUMERIC / COUNT(*)::NUMERIC) * 100, 2)
            ELSE 0 
        END as success_rate,
        ROUND(AVG(fusion_score)::NUMERIC, 3) as avg_fusion_score,
        MAX(auth_timestamp) as last_auth_timestamp
    FROM biometric_auth_log
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_user_auth_stats IS 'Get authentication statistics for a user';

-- Function to detect suspicious activity (multiple failed attempts)
CREATE OR REPLACE FUNCTION detect_suspicious_auth_activity(
    p_user_id INTEGER,
    p_time_window_minutes INTEGER DEFAULT 15,
    p_failure_threshold INTEGER DEFAULT 5
)
RETURNS BOOLEAN AS $$
DECLARE
    failed_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO failed_count
    FROM biometric_auth_log
    WHERE user_id = p_user_id
    AND authenticated = false
    AND auth_timestamp >= NOW() - (p_time_window_minutes || ' minutes')::INTERVAL;
    
    RETURN failed_count >= p_failure_threshold;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION detect_suspicious_auth_activity IS 'Detect if user has too many failed auth attempts in recent time window';

-- ============================================================================
-- STEP 5: Create View for Easy Querying (Optional)
-- ============================================================================

-- View combining user info with their latest biometric auth
CREATE OR REPLACE VIEW user_biometric_status AS
SELECT 
    u.id,
    u.username,
    u.email,
    u.biometric_registered_at,
    CASE 
        WHEN u.face_biometric IS NOT NULL 
         AND u.hand_biometric IS NOT NULL 
         AND u.style_biometric IS NOT NULL 
        THEN true 
        ELSE false 
    END as has_biometrics,
    (SELECT COUNT(*) FROM biometric_auth_log WHERE user_id = u.id) as total_auth_attempts,
    (SELECT COUNT(*) FROM biometric_auth_log WHERE user_id = u.id AND authenticated = true) as successful_auths,
    (SELECT MAX(auth_timestamp) FROM biometric_auth_log WHERE user_id = u.id) as last_auth_timestamp,
    (SELECT AVG(fusion_score) FROM biometric_auth_log WHERE user_id = u.id) as avg_fusion_score
FROM users u;

COMMENT ON VIEW user_biometric_status IS 'Summary view of user biometric enrollment and authentication stats';

-- ============================================================================
-- VERIFICATION QUERIES (Run these to check if everything worked)
-- ============================================================================

-- Check if columns were added to users table
SELECT 
    column_name, 
    data_type, 
    is_nullable 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('face_biometric', 'hand_biometric', 'style_biometric', 'biometric_registered_at')
ORDER BY column_name;

-- Check if biometric_auth_log table exists
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_name = 'biometric_auth_log'
) as table_exists;

-- Check if indexes were created
SELECT 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE tablename = 'biometric_auth_log'
ORDER BY indexname;

-- Check if functions were created
SELECT 
    proname as function_name, 
    pg_get_functiondef(oid) as definition
FROM pg_proc 
WHERE proname IN ('user_has_biometrics', 'get_user_auth_stats', 'detect_suspicious_auth_activity');

-- ============================================================================
-- SAMPLE QUERIES (For testing and usage examples)
-- ============================================================================

-- Example 1: Check which users have enrolled biometrics
SELECT 
    id, 
    username, 
    email,
    biometric_registered_at,
    CASE 
        WHEN face_biometric IS NOT NULL 
         AND hand_biometric IS NOT NULL 
         AND style_biometric IS NOT NULL 
        THEN 'Enrolled' 
        ELSE 'Not Enrolled' 
    END as biometric_status
FROM users
ORDER BY biometric_registered_at DESC NULLS LAST;

-- Example 2: View recent authentication attempts
SELECT 
    bal.id,
    u.username,
    bal.auth_type,
    bal.fusion_score,
    bal.authenticated,
    bal.auth_timestamp
FROM biometric_auth_log bal
JOIN users u ON bal.user_id = u.id
ORDER BY bal.auth_timestamp DESC
LIMIT 20;

-- Example 3: Get authentication stats for a specific user (replace 1 with actual user_id)
SELECT * FROM get_user_auth_stats(1);

-- Example 4: Check if user has biometrics enrolled (replace 1 with actual user_id)
SELECT user_has_biometrics(1) as has_biometrics;

-- Example 5: View all users with biometric status
SELECT * FROM user_biometric_status
ORDER BY biometric_registered_at DESC NULLS LAST;

-- Example 6: Find users with suspicious activity (multiple failed attempts)
SELECT 
    u.id,
    u.username,
    detect_suspicious_auth_activity(u.id, 15, 5) as is_suspicious,
    (SELECT COUNT(*) FROM biometric_auth_log WHERE user_id = u.id AND authenticated = false AND auth_timestamp >= NOW() - INTERVAL '15 minutes') as recent_failures
FROM users u
WHERE EXISTS (SELECT 1 FROM biometric_auth_log WHERE user_id = u.id)
ORDER BY recent_failures DESC;

-- ============================================================================
-- ROLLBACK INSTRUCTIONS (If you need to undo these changes)
-- ============================================================================

/*
-- CAUTION: Only run these if you want to REMOVE the biometric features

-- Drop view
DROP VIEW IF EXISTS user_biometric_status;

-- Drop functions
DROP FUNCTION IF EXISTS user_has_biometrics(INTEGER);
DROP FUNCTION IF EXISTS get_user_auth_stats(INTEGER);
DROP FUNCTION IF EXISTS detect_suspicious_auth_activity(INTEGER, INTEGER, INTEGER);

-- Drop indexes (will be auto-dropped with table)
DROP INDEX IF EXISTS idx_biometric_auth_log_user_id;
DROP INDEX IF EXISTS idx_biometric_auth_log_timestamp;
DROP INDEX IF EXISTS idx_biometric_auth_log_failed;
DROP INDEX IF EXISTS idx_biometric_auth_log_type;
DROP INDEX IF EXISTS idx_biometric_auth_log_user_transaction;

-- Drop table
DROP TABLE IF EXISTS biometric_auth_log;

-- Remove columns from users table
ALTER TABLE users DROP COLUMN IF EXISTS face_biometric;
ALTER TABLE users DROP COLUMN IF EXISTS hand_biometric;
ALTER TABLE users DROP COLUMN IF EXISTS style_biometric;
ALTER TABLE users DROP COLUMN IF EXISTS biometric_registered_at;
*/

-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Biometric Schema Update Complete!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Added to users table:';
    RAISE NOTICE '  - face_biometric (TEXT)';
    RAISE NOTICE '  - hand_biometric (TEXT)';
    RAISE NOTICE '  - style_biometric (TEXT)';
    RAISE NOTICE '  - biometric_registered_at (TIMESTAMP)';
    RAISE NOTICE '';
    RAISE NOTICE 'Created tables:';
    RAISE NOTICE '  - biometric_auth_log (with 5 indexes)';
    RAISE NOTICE '';
    RAISE NOTICE 'Created helper functions:';
    RAISE NOTICE '  - user_has_biometrics()';
    RAISE NOTICE '  - get_user_auth_stats()';
    RAISE NOTICE '  - detect_suspicious_auth_activity()';
    RAISE NOTICE '';
    RAISE NOTICE 'Created views:';
    RAISE NOTICE '  - user_biometric_status';
    RAISE NOTICE '';
    RAISE NOTICE 'Run verification queries above to confirm!';
    RAISE NOTICE '========================================';
END $$;
