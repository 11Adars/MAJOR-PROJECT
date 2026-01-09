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

// Submit support ticket using hybrid sign language recognition + query generation
const submitHybridSignTicket = async (req, res) => {
  try {
    const userId = req.userId;
    const { 
      frames,                    // Array of base64-encoded frames
      use_slm = true,           // Whether to use SLM for query generation
      return_skeleton = false   // NEW: Return frames with skeleton visualization
    } = req.body;

    if (!frames || !Array.isArray(frames) || frames.length < 10) {
      return res.status(400).json({ 
        message: 'At least 10 frames required for sign recognition' 
      });
    }

    // Call NS-AGF API for hybrid recognition
    const axios = require('axios');
    const NS_AGF_API = process.env.NS_AGF_API || 'http://127.0.0.1:5003';

    console.log(`\n📞 Calling NS-AGF hybrid endpoint...`);
    console.log(`   Frames: ${frames.length}, SLM: ${use_slm}, Skeleton: ${return_skeleton}`);
    
    const hybridResponse = await axios.post(
      `${NS_AGF_API}/api/sign/hybrid-recognize`,
      {
        frames: frames,
        use_slm: use_slm,
        return_skeleton: return_skeleton  // NEW: Pass skeleton option
      },
      {
        timeout: 30000,  // 30 second timeout for SLM processing
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );

    if (!hybridResponse.data.success) {
      return res.status(400).json({
        message: 'Failed to recognize sign language',
        details: hybridResponse.data.error,
        confidence: hybridResponse.data.confidence || 0,
        frames_processed: hybridResponse.data.frames_processed || 0
      });
    }

    const recognitionResult = hybridResponse.data;
    
    console.log(`\n✅ Sign recognized: ${recognitionResult.sign}`);
    console.log(`   Confidence: ${recognitionResult.confidence.toFixed(3)}`);
    console.log(`   Intent: ${recognitionResult.intent}`);
    console.log(`   Query: ${recognitionResult.query}`);
    console.log(`   SLM used: ${recognitionResult.slm_used}`);

    // Get user details
    const userResult = await pool.query(
      'SELECT username, email FROM users WHERE id = $1',
      [userId]
    );

    if (userResult.rows.length === 0) {
      return res.status(404).json({ message: 'User not found' });
    }

    const user = userResult.rows[0];

    // Insert ticket into database with sign language details
    const ticketResult = await pool.query(
      `INSERT INTO support_tickets 
        (user_id, user_email, query_text, query_source, status, 
         sign_recognized, intent_detected, slm_used, confidence_score)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
       RETURNING id, query_text, status, created_at`,
      [
        userId,
        user.email,
        recognitionResult.query,          // Generated query
        'sign_language_hybrid',            // Source
        'pending',                         // Initial status
        recognitionResult.sign,            // Sign name
        recognitionResult.intent,          // Intent type
        recognitionResult.slm_used,        // Whether SLM was used
        recognitionResult.confidence       // Confidence score
      ]
    );

    const ticket = ticketResult.rows[0];

    console.log(`\n💾 Ticket created: ID=${ticket.id}`);

    // Send email to bank support
    const bankEmailSent = await sendQueryToBank(
      user.email,
      user.username,
      `[SIGN LANGUAGE] ${recognitionResult.sign}\nIntent: ${recognitionResult.intent}\n\nQuery: ${recognitionResult.query}`,
      ticket.id
    );

    // Send confirmation to user
    const userEmailSent = await sendQueryConfirmation(
      user.email,
      user.username,
      recognitionResult.query,
      ticket.id
    );

    res.status(201).json({
      message: 'Support ticket submitted via sign language',
      ticket: {
        id: ticket.id,
        query_text: ticket.query_text,
        status: ticket.status,
        created_at: ticket.created_at
      },
      sign_language_data: {
        sign_recognized: recognitionResult.sign,
        confidence: recognitionResult.confidence,
        intent: recognitionResult.intent,
        is_banking_intent: recognitionResult.is_banking_intent,
        query_generated: recognitionResult.query,
        slm_used: recognitionResult.slm_used,
        frames_processed: recognitionResult.frames_processed,
        valid_frames: recognitionResult.valid_frames,
        // Include skeleton frames if available for debugging
        skeleton_frames: recognitionResult.skeleton_frames || []
      },
      emails_sent: {
        to_bank: bankEmailSent,
        to_user: userEmailSent
      }
    });

  } catch (error) {
    console.error('Error submitting hybrid sign ticket:', error);
    
    // Handle specific errors
    if (error.code === 'ECONNREFUSED') {
      return res.status(503).json({ 
        message: 'Sign language service unavailable',
        details: 'NS-AGF service not running on port 5003'
      });
    }
    
    if (error.response && error.response.data) {
      return res.status(error.response.status || 500).json({
        message: 'Sign language recognition failed',
        details: error.response.data.error || error.message
      });
    }
    
    res.status(500).json({ 
      message: 'Failed to submit support ticket', 
      error: error.message 
    });
  }
};

// ============================================================================
// NEW: Submit ticket from multi-sign sentence (no automatic email)
// ============================================================================
const submitHybridSignSentence = async (req, res) => {
  try {
    const userId = req.userId;
    const { 
      sentence,      // Complete sentence from multiple signs
      words,         // Array of individual recognized words
      use_slm = true // Whether to use SLM for query enhancement
    } = req.body;

    if (!sentence || sentence.trim().length === 0) {
      return res.status(400).json({ 
        message: 'Sentence is required' 
      });
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

    console.log(`\n📝 Processing sign sentence: "${sentence}"`);
    console.log(`   Words: [${words.join(', ')}]`);
    console.log(`   SLM enabled: ${use_slm}`);

    // Call SLM for intent analysis and query generation
    const axios = require('axios');
    let generatedQuery = sentence;
    let intent = 'general_inquiry';
    let slmUsed = false;

    if (use_slm) {
      try {
        console.log(`📝 Calling SLM endpoint with sentence: "${sentence}"`);
        const slmResponse = await axios.post(
          'http://127.0.0.1:5003/api/slm/generate',
          { 
            sign_word: sentence,
            context: `User performed signs: ${words.join(', ')}`
          },
          { timeout: 30000 }  // Increased to 30 seconds for SLM generation
        );

        console.log(`   Response status: ${slmResponse.status}`);
        console.log(`   Response data:`, slmResponse.data);

        if (slmResponse.data && slmResponse.data.query) {
          generatedQuery = slmResponse.data.query;
          intent = slmResponse.data.intent || 'general_inquiry';
          slmUsed = true;
          console.log(`✅ SLM generated query: "${generatedQuery}"`);
          console.log(`   Intent: ${intent}`);
          console.log(`   SLM Used: ${slmUsed}`);
        } else {
          console.warn(`⚠️ No query field in SLM response. Using fallback.`);
          console.warn(`   Response:`, slmResponse.data);
        }
      } catch (slmError) {
        console.error('❌ SLM generation error:');
        console.error(`   Message: ${slmError.message}`);
        console.error(`   Code: ${slmError.code}`);
        if (slmError.response) {
          console.error(`   Status: ${slmError.response.status}`);
          console.error(`   Data:`, slmError.response.data);
        } else if (slmError.request) {
          console.error(`   Request: No response received`);
        }
        console.warn(`⚠️ Falling back to raw sentence: "${sentence}"`);
      }
    }

    // Insert ticket into database
    const ticketResult = await pool.query(
      `INSERT INTO support_tickets (user_id, user_email, query_text, query_source, status) 
       VALUES ($1, $2, $3, 'sign_language', 'pending') 
       RETURNING id, query_text, status, created_at`,
      [userId, user.email, generatedQuery.trim()]
    );

    const ticket = ticketResult.rows[0];

    console.log(`✅ Ticket created: ID=${ticket.id}`);
    console.log(`   Query: "${generatedQuery}"`);
    console.log(`   User: ${user.username} (${user.email})`);

    // Send email to bank support
    let bankEmailSent = false;
    let userEmailSent = false;

    try {
      console.log(`\n📧 Attempting to send email to bank support...`);
      console.log(`   From: ${process.env.EMAIL_USER}`);
      console.log(`   To: ${process.env.BANK_SUPPORT_EMAIL}`);
      console.log(`   Ticket ID: #${ticket.id}`);
      
      bankEmailSent = await sendQueryToBank(
        user.email,
        user.username,
        generatedQuery.trim(),
        ticket.id
      );
      
      if (bankEmailSent) {
        console.log(`✅ Bank email sent successfully!`);
      } else {
        console.log(`❌ Bank email failed (returned false)`);
      }
    } catch (emailError) {
      console.error('❌ Exception while sending email to bank:');
      console.error(`   Error: ${emailError.message}`);
      console.error(`   Stack: ${emailError.stack}`);
    }

    // Send confirmation to user
    try {
      console.log(`\n📧 Attempting to send confirmation to user...`);
      console.log(`   From: ${process.env.EMAIL_USER}`);
      console.log(`   To: ${user.email}`);
      console.log(`   Ticket ID: #${ticket.id}`);
      
      userEmailSent = await sendQueryConfirmation(
        user.email,
        user.username,
        generatedQuery.trim(),
        ticket.id
      );
      
      if (userEmailSent) {
        console.log(`✅ User confirmation email sent successfully!`);
      } else {
        console.log(`❌ User confirmation email failed (returned false)`);
      }
    } catch (emailError) {
      console.error('❌ Exception while sending confirmation to user:');
      console.error(`   Error: ${emailError.message}`);
      console.error(`   Stack: ${emailError.stack}`);
    }

    console.log(`\n📊 Email Summary:`);
    console.log(`   Bank email sent: ${bankEmailSent}`);
    console.log(`   User email sent: ${userEmailSent}\n`);

    res.status(201).json({
      message: 'Support ticket created successfully',
      ticket: {
        id: ticket.id,
        query_text: ticket.query_text,
        status: ticket.status,
        created_at: ticket.created_at
      },
      sign_language_data: {
        original_sentence: sentence,
        words: words,
        query_generated: generatedQuery,
        intent: intent,
        slm_used: slmUsed
      },
      emails_sent: {
        to_bank: bankEmailSent,
        to_user: userEmailSent
      }
    });

  } catch (error) {
    console.error('Error processing sign sentence:', error);
    res.status(500).json({ 
      message: 'Failed to create support ticket', 
      error: error.message 
    });
  }
};

module.exports = {
  submitTicket,
  getUserTickets,
  getTicketDetails,
  addTicketResponse,
  resolveTicket,
  getTicketStats,
  submitHybridSignTicket,
  submitHybridSignSentence
};
