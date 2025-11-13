-- Support Tickets System for Sign Language Queries
-- Run this SQL in your PostgreSQL database

-- Create support_tickets table
CREATE TABLE IF NOT EXISTS support_tickets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    user_email VARCHAR(255) NOT NULL,
    query_text TEXT NOT NULL,
    query_source VARCHAR(50) DEFAULT 'sign_language',
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create ticket_responses table
CREATE TABLE IF NOT EXISTS ticket_responses (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER REFERENCES support_tickets(id) ON DELETE CASCADE,
    response_text TEXT NOT NULL,
    response_from VARCHAR(100) DEFAULT 'bank_support',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_tickets_user_id ON support_tickets(user_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON support_tickets(status);
CREATE INDEX IF NOT EXISTS idx_responses_ticket_id ON ticket_responses(ticket_id);

-- Add comments
COMMENT ON TABLE support_tickets IS 'Stores customer support queries from sign language and other sources';
COMMENT ON TABLE ticket_responses IS 'Stores bank responses to customer support tickets';

-- Sample data (optional - for testing)
-- You can remove this section if you don't want test data

-- Note: Make sure you have a test user with id=1 before inserting test data
-- INSERT INTO support_tickets (user_id, user_email, query_text, status) 
-- VALUES (1, 'test@example.com', 'I need help with my account balance', 'pending');
