-- ============================================================================
-- Database Schema Update for Multi-Factor Authentication
-- ============================================================================
-- 
-- This SQL script adds multi-factor authentication support (Face, Voice, OTP)
-- Run this in your PostgreSQL/Supabase SQL console.
--
-- Features:
-- 1. OTP columns in users table for login authentication
-- 2. Temporary registrations table for OTP verification during signup
-- 3. Phone number support
-- 4. Voice registration tracking
-- 5. OTP verification status
--
-- Author: NS-AGF Banking System Team
-- Date: January 2026
-- Database: PostgreSQL (Supabase)
--
-- ============================================================================

-- ============================================================================
-- STEP 1: Add Multi-Auth Columns to Users Table
-- ============================================================================

-- Add phone number
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS phone VARCHAR(20);

-- Add OTP columns for login
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS otp VARCHAR(6);

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS otp_expires TIMESTAMP;

-- Add OTP verification status
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS otp_verified BOOLEAN DEFAULT FALSE;

-- Add voice registration flag (if not exists)
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS voice_registered BOOLEAN DEFAULT FALSE;

-- Add voice data column (JSONB for storing embeddings and features)
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS voice_data JSONB;

-- Add face embedding column (for face authentication)
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS face_embedding JSONB;

-- Add comments for documentation
COMMENT ON COLUMN users.phone IS 'User phone number for contact';
COMMENT ON COLUMN users.otp IS 'One-time password for login authentication (6 digits)';
COMMENT ON COLUMN users.otp_expires IS 'OTP expiration timestamp (valid for 5 minutes)';
COMMENT ON COLUMN users.otp_verified IS 'Whether user has verified their email via OTP';
COMMENT ON COLUMN users.voice_registered IS 'Whether user has registered voice authentication';
COMMENT ON COLUMN users.voice_data IS 'Voice biometric data (embeddings and features)';
COMMENT ON COLUMN users.face_embedding IS 'Face biometric embedding (512-dim vector)';

-- ============================================================================
-- STEP 2: Create Temporary Registrations Table
-- ============================================================================

-- This table stores OTP for registration process
CREATE TABLE IF NOT EXISTS temp_registrations (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    otp VARCHAR(6) NOT NULL,
    otp_expires TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add comments
COMMENT ON TABLE temp_registrations IS 'Temporary storage for registration OTPs';
COMMENT ON COLUMN temp_registrations.otp IS 'One-time password sent to email during registration';
COMMENT ON COLUMN temp_registrations.otp_expires IS 'OTP expiration timestamp (valid for 5 minutes)';

-- ============================================================================
-- STEP 3: Create Indexes for Performance
-- ============================================================================

-- Index for OTP lookup during login
CREATE INDEX IF NOT EXISTS idx_users_otp 
ON users(email, otp) 
WHERE otp IS NOT NULL;

-- Index for OTP expiration cleanup
CREATE INDEX IF NOT EXISTS idx_users_otp_expires 
ON users(otp_expires) 
WHERE otp_expires IS NOT NULL;

-- Index for temp registrations OTP lookup
CREATE INDEX IF NOT EXISTS idx_temp_registrations_email 
ON temp_registrations(email);

-- Index for voice authentication lookup
CREATE INDEX IF NOT EXISTS idx_users_voice_registered 
ON users(username) 
WHERE voice_registered = TRUE;

-- ============================================================================
-- STEP 4: Update Login History Table
-- ============================================================================

-- Add new auth method types if login_history table exists
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'login_history') THEN
        -- Check if auth_method column exists and update check constraint
        IF EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'login_history' AND column_name = 'auth_method') THEN
            
            -- Drop existing constraint if it exists
            ALTER TABLE login_history DROP CONSTRAINT IF EXISTS login_history_auth_method_check;
            
            -- Add new constraint with additional auth methods
            ALTER TABLE login_history 
            ADD CONSTRAINT login_history_auth_method_check 
            CHECK (auth_method IN ('face', 'voice', 'otp', 'multi_auth_register', 'biometric', 'logout'));
        END IF;
    END IF;
END $$;

-- ============================================================================
-- STEP 5: Auto-Cleanup for Expired OTPs (Optional)
-- ============================================================================

-- Function to clean up expired OTPs in users table
CREATE OR REPLACE FUNCTION cleanup_expired_otps()
RETURNS void AS $$
BEGIN
    UPDATE users 
    SET otp = NULL, otp_expires = NULL 
    WHERE otp_expires < NOW() AND otp IS NOT NULL;
    
    DELETE FROM temp_registrations 
    WHERE otp_expires < NOW();
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled job to run cleanup (requires pg_cron extension)
-- Uncomment if you have pg_cron enabled:
-- SELECT cron.schedule('cleanup-expired-otps', '*/5 * * * *', 'SELECT cleanup_expired_otps()');

-- ============================================================================
-- STEP 6: Verification Queries
-- ============================================================================

-- Check if columns were added successfully
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('phone', 'otp', 'otp_expires', 'otp_verified', 'voice_registered', 'voice_data', 'face_embedding')
ORDER BY column_name;

-- Check if temp_registrations table was created
SELECT EXISTS (
    SELECT 1 
    FROM information_schema.tables 
    WHERE table_name = 'temp_registrations'
) AS temp_registrations_exists;

-- Check if indexes were created
SELECT 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE tablename IN ('users', 'temp_registrations')
AND indexname LIKE '%otp%' OR indexname LIKE '%voice%'
ORDER BY indexname;

-- ============================================================================
-- STEP 7: Sample Queries for Testing
-- ============================================================================

-- Test: Insert a temporary registration OTP
-- INSERT INTO temp_registrations (email, otp, otp_expires)
-- VALUES ('test@example.com', '123456', NOW() + INTERVAL '5 minutes');

-- Test: Update user with OTP for login
-- UPDATE users 
-- SET otp = '654321', otp_expires = NOW() + INTERVAL '5 minutes'
-- WHERE email = 'test@example.com';

-- Test: Query user auth methods
-- SELECT 
--     username, 
--     email, 
--     voice_registered,
--     otp_verified,
--     CASE WHEN face_embedding IS NOT NULL THEN TRUE ELSE FALSE END AS face_registered
-- FROM users 
-- WHERE username = 'testuser';

-- ============================================================================
-- STEP 8: Rollback Instructions (if needed)
-- ============================================================================

-- To rollback these changes, run:
/*
-- Drop temp_registrations table
DROP TABLE IF EXISTS temp_registrations CASCADE;

-- Drop function
DROP FUNCTION IF EXISTS cleanup_expired_otps() CASCADE;

-- Remove columns from users table
ALTER TABLE users DROP COLUMN IF EXISTS phone;
ALTER TABLE users DROP COLUMN IF EXISTS otp;
ALTER TABLE users DROP COLUMN IF EXISTS otp_expires;
ALTER TABLE users DROP COLUMN IF EXISTS otp_verified;
ALTER TABLE users DROP COLUMN IF EXISTS voice_registered;
ALTER TABLE users DROP COLUMN IF EXISTS voice_data;
ALTER TABLE users DROP COLUMN IF EXISTS face_embedding;

-- Drop indexes
DROP INDEX IF EXISTS idx_users_otp;
DROP INDEX IF EXISTS idx_users_otp_expires;
DROP INDEX IF EXISTS idx_temp_registrations_email;
DROP INDEX IF EXISTS idx_users_voice_registered;
*/

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

SELECT '✅ Multi-Factor Authentication Schema Update Complete!' AS status;
SELECT '📝 You can now use Face + Voice + OTP authentication' AS info;
SELECT '🔐 Users table updated with new auth columns' AS detail_1;
SELECT '📧 Temporary registrations table created for signup OTPs' AS detail_2;
SELECT '⚡ Indexes created for optimal query performance' AS detail_3;
