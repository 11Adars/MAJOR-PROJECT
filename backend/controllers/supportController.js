const pool = require('../db');
const { sendQueryToBank, sendQueryConfirmation, notifyUserOfResponse } = require('../utils/emailService');

// Submit a new support ticket (from sign language or manual)
const submitTicket = async (req, res) => {
  try {
    const userId = req.userId; // Changed from req.user.id to match authMiddleware
    const { query_text, query_source = 'sign_language' } = req.body;

    if (!query_text || query_text.trim().length === 0) {
      return res.status(400).json({ message: 'Query text is required' });
    }

    // Get user details
    const userResult = await pool.query(
      'SELECT username, email FROM users WHERE id = $1',
      [userId]
    );

    if (userResult.rows.length === 0) {
      return res.status(404).json({ message: 'User not found' });
    }

    const user = userResult.rows[0];

    // Insert ticket into database
    const ticketResult = await pool.query(
      `INSERT INTO support_tickets (user_id, user_email, query_text, query_source, status) 
       VALUES ($1, $2, $3, $4, 'pending') 
       RETURNING id, query_text, status, created_at`,
      [userId, user.email, query_text.trim(), query_source]
    );

    const ticket = ticketResult.rows[0];

    // Send email to bank support
    const bankEmailSent = await sendQueryToBank(
      user.email,
      user.username,
      query_text.trim(),
      ticket.id
    );

    // Send confirmation to user
    const userEmailSent = await sendQueryConfirmation(
      user.email,
      user.username,
      query_text.trim(),
      ticket.id
    );

    res.status(201).json({
      message: 'Support ticket submitted successfully',
      ticket: {
        id: ticket.id,
        query_text: ticket.query_text,
        status: ticket.status,
        created_at: ticket.created_at
      },
      emails_sent: {
        to_bank: bankEmailSent,
        to_user: userEmailSent
      }
    });
  } catch (error) {
    console.error('Error submitting ticket:', error);
    res.status(500).json({ message: 'Failed to submit support ticket', error: error.message });
  }
};

// Get all tickets for the logged-in user
const getUserTickets = async (req, res) => {
  try {
    const userId = req.userId; // Changed from req.user.id to match authMiddleware
    const { status, limit = 50 } = req.query;

    let query = `
      SELECT 
        t.id,
        t.query_text,
        t.query_source,
        t.status,
        t.created_at,
        t.updated_at,
        COUNT(r.id) as response_count
      FROM support_tickets t
      LEFT JOIN ticket_responses r ON t.id = r.ticket_id
      WHERE t.user_id = $1
    `;

    const params = [userId];

    if (status) {
      query += ` AND t.status = $2`;
      params.push(status);
    }

    query += `
      GROUP BY t.id
      ORDER BY t.created_at DESC
      LIMIT $${params.length + 1}
    `;
    params.push(limit);

    const result = await pool.query(query, params);

    res.json({
      tickets: result.rows,
      total: result.rows.length
    });
  } catch (error) {
    console.error('Error fetching tickets:', error);
    res.status(500).json({ message: 'Failed to fetch tickets', error: error.message });
  }
};

// Get a specific ticket with all its responses
const getTicketDetails = async (req, res) => {
  try {
    const userId = req.userId; // Changed from req.user.id to match authMiddleware
    const ticketId = req.params.ticketId;

    // Get ticket details
    const ticketResult = await pool.query(
      `SELECT id, query_text, query_source, status, created_at, updated_at 
       FROM support_tickets 
       WHERE id = $1 AND user_id = $2`,
      [ticketId, userId]
    );

    if (ticketResult.rows.length === 0) {
      return res.status(404).json({ message: 'Ticket not found' });
    }

    const ticket = ticketResult.rows[0];

    // Get all responses for this ticket
    const responsesResult = await pool.query(
      `SELECT id, response_text, response_from, created_at 
       FROM ticket_responses 
       WHERE ticket_id = $1 
       ORDER BY created_at ASC`,
      [ticketId]
    );

    res.json({
      ticket: {
        ...ticket,
        responses: responsesResult.rows
      }
    });
  } catch (error) {
    console.error('Error fetching ticket details:', error);
    res.status(500).json({ message: 'Failed to fetch ticket details', error: error.message });
  }
};

// Add a response to a ticket (for bank support - requires admin check in production)
const addTicketResponse = async (req, res) => {
  try {
    const ticketId = req.params.ticketId;
    const { response_text, response_from = 'bank_support' } = req.body;

    if (!response_text || response_text.trim().length === 0) {
      return res.status(400).json({ message: 'Response text is required' });
    }

    // Get ticket and user details
    const ticketResult = await pool.query(
      `SELECT t.id, t.query_text, t.user_id, u.email, u.username 
       FROM support_tickets t
       JOIN users u ON t.user_id = u.id
       WHERE t.id = $1`,
      [ticketId]
    );

    if (ticketResult.rows.length === 0) {
      return res.status(404).json({ message: 'Ticket not found' });
    }

    const ticket = ticketResult.rows[0];

    // Insert response
    const responseResult = await pool.query(
      `INSERT INTO ticket_responses (ticket_id, response_text, response_from) 
       VALUES ($1, $2, $3) 
       RETURNING id, response_text, response_from, created_at`,
      [ticketId, response_text.trim(), response_from]
    );

    // Update ticket status to 'responded'
    await pool.query(
      `UPDATE support_tickets 
       SET status = 'responded', updated_at = CURRENT_TIMESTAMP 
       WHERE id = $1`,
      [ticketId]
    );

    // Notify user via email
    await notifyUserOfResponse(
      ticket.email,
      ticket.username,
      ticket.query_text,
      response_text.trim(),
      ticketId
    );

    res.status(201).json({
      message: 'Response added successfully',
      response: responseResult.rows[0]
    });
  } catch (error) {
    console.error('Error adding response:', error);
    res.status(500).json({ message: 'Failed to add response', error: error.message });
  }
};

// Mark ticket as resolved
const resolveTicket = async (req, res) => {
  try {
    const userId = req.userId; // Changed from req.user.id to match authMiddleware
    const ticketId = req.params.ticketId;

    const result = await pool.query(
      `UPDATE support_tickets 
       SET status = 'resolved', updated_at = CURRENT_TIMESTAMP 
       WHERE id = $1 AND user_id = $2 
       RETURNING id, status`,
      [ticketId, userId]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ message: 'Ticket not found' });
    }

    res.json({
      message: 'Ticket marked as resolved',
      ticket: result.rows[0]
    });
  } catch (error) {
    console.error('Error resolving ticket:', error);
    res.status(500).json({ message: 'Failed to resolve ticket', error: error.message });
  }
};

// Get ticket statistics for user
const getTicketStats = async (req, res) => {
  try {
    const userId = req.userId; // Changed from req.user.id to match authMiddleware

    const result = await pool.query(
      `SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
        COUNT(CASE WHEN status = 'responded' THEN 1 END) as responded,
        COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved
       FROM support_tickets 
       WHERE user_id = $1`,
      [userId]
    );

    res.json(result.rows[0]);
  } catch (error) {
    console.error('Error fetching stats:', error);
    res.status(500).json({ message: 'Failed to fetch statistics', error: error.message });
  }
};

module.exports = {
  submitTicket,
  getUserTickets,
  getTicketDetails,
  addTicketResponse,
  resolveTicket,
  getTicketStats
};
