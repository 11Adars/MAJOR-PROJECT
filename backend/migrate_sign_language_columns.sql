-- Migration script to add sign language columns to support_tickets table
-- Run this if you already have the support_tickets table created

-- Add new columns if they don't exist
ALTER TABLE support_tickets
ADD COLUMN IF NOT EXISTS sign_recognized VARCHAR(255),
ADD COLUMN IF NOT EXISTS intent_detected VARCHAR(100),
ADD COLUMN IF NOT EXISTS slm_used BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS confidence_score DECIMAL(3, 2);

-- Add index on sign_recognized for faster queries
CREATE INDEX IF NOT EXISTS idx_tickets_sign ON support_tickets(sign_recognized);
CREATE INDEX IF NOT EXISTS idx_tickets_intent ON support_tickets(intent_detected);

-- Verify the columns were added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'support_tickets'
ORDER BY ordinal_position;
