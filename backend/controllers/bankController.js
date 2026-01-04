const pool = require('../db');
const bcrypt = require('bcrypt');
const razorpay = require('../razorpay');
const biometricService = require('../services/biometricService');

// 1. Set or update PIN
exports.setPin = async (req, res) => {
  const { pin } = req.body;
  const userId = req.userId;

  if (!pin || pin.length < 4) {
    return res.status(400).json({ message: 'PIN must be at least 4 digits.' });
  }

  try {
    const pinHash = await bcrypt.hash(pin, 10);
    await pool.query(
      `INSERT INTO user_pins (user_id, pin_hash)
       VALUES ($1, $2)
       ON CONFLICT (user_id) DO UPDATE SET pin_hash = EXCLUDED.pin_hash`,
      [userId, pinHash]
    );
    res.json({ message: 'PIN set successfully.' });
  } catch (err) {
    console.error('Set PIN error:', err);
    res.status(500).json({ message: 'Failed to set PIN.' });
  }
};

// 2. Verify PIN
exports.verifyPin = async (req, res) => {
  const { pin } = req.body;
  const userId = req.userId;

  try {
    const result = await pool.query(
      'SELECT pin_hash FROM user_pins WHERE user_id = $1',
      [userId]
    );
    if (result.rows.length === 0) {
      return res.status(404).json({ message: 'PIN not set.' });
    }
    const isMatch = await bcrypt.compare(pin, result.rows[0].pin_hash);
    if (!isMatch) {
      return res.status(401).json({ message: 'Incorrect PIN.' });
    }
    res.json({ message: 'PIN verified.' });
  } catch (err) {
    console.error('Verify PIN error:', err);
    res.status(500).json({ message: 'Failed to verify PIN.' });
  }
};

// 3. Get Balance
exports.getBalance = async (req, res) => {
  const userId = req.userId;
  try {
    const result = await pool.query(
      'SELECT balance, account_number FROM accounts WHERE user_id = $1',
      [userId]
    );
    if (result.rows.length === 0) {
      return res.status(404).json({ message: 'Account not found.' });
    }
    res.json(result.rows[0]);
  } catch (err) {
    console.error('Get balance error:', err);
    res.status(500).json({ message: 'Failed to get balance.' });
  }
};

// 4. Add Beneficiary
exports.addBeneficiary = async (req, res) => {
  const userId = req.userId;
  const { name, account_number, ifsc } = req.body;
    // Input validation
  if (!name || typeof name !== 'string' || name.length < 2) {
    return res.status(400).json({ message: 'Name is required and must be at least 2 characters.' });
  }
  if (!account_number || !/^\d{9,18}$/.test(account_number)) {
    return res.status(400).json({ message: 'Account number must be 9-18 digits.' });
  }
  if (!ifsc || !/^[A-Z]{4}0[A-Z0-9]{6}$/.test(ifsc)) {
    return res.status(400).json({ message: 'Invalid IFSC code.' });
  }

  try {
    await pool.query(
      `INSERT INTO beneficiaries (user_id, name, account_number, ifsc)
       VALUES ($1, $2, $3, $4)`,
      [userId, name, account_number, ifsc]
    );
    res.json({ message: 'Beneficiary added.' });
  } catch (err) {
    console.error('Add beneficiary error:', err);
    res.status(500).json({ message: 'Failed to add beneficiary.' });
  }
};

// 5. List Beneficiaries
exports.listBeneficiaries = async (req, res) => {
  const userId = req.userId;
  try {
    const result = await pool.query(
      'SELECT id, name, account_number, ifsc FROM beneficiaries WHERE user_id = $1',
      [userId]
    );
    res.json(result.rows);
  } catch (err) {
    console.error('List beneficiaries error:', err);
    res.status(500).json({ message: 'Failed to fetch beneficiaries.' });
  }
};

// 6. Transfer (Simulated with RazorpayX payout logic)
exports.transfer = async (req, res) => {
  const userId = req.userId;
  const { amount, beneficiary_id, pin } = req.body;


  // Input validation
  if (!beneficiary_id || isNaN(Number(beneficiary_id))) {
    return res.status(400).json({ message: 'Valid beneficiary is required.' });
  }
  if (!amount || isNaN(Number(amount)) || Number(amount) <= 0) {
    return res.status(400).json({ message: 'Amount must be a positive number.' });
  }
  if (!pin || typeof pin !== 'string' || pin.length < 4) {
    return res.status(400).json({ message: 'PIN must be at least 4 digits.' });
  }

  // Verify PIN
  try {
    const pinResult = await pool.query(
      'SELECT pin_hash FROM user_pins WHERE user_id = $1',
      [userId]
    );
    if (pinResult.rows.length === 0) {
      return res.status(404).json({ message: 'PIN not set.' });
    }
    const isMatch = await bcrypt.compare(pin, pinResult.rows[0].pin_hash);
    if (!isMatch) {
      return res.status(401).json({ message: 'Incorrect PIN.' });
    }
  } catch (err) {
    return res.status(500).json({ message: 'PIN verification failed.' });
  }

  // Get user account and beneficiary
  try {
    const accountResult = await pool.query(
      'SELECT id, balance, account_number FROM accounts WHERE user_id = $1',
      [userId]
    );
    if (accountResult.rows.length === 0) {
      return res.status(404).json({ message: 'Account not found.' });
    }
    const account = accountResult.rows[0];

    if (parseFloat(account.balance) < parseFloat(amount)) {
      return res.status(400).json({ message: 'Insufficient balance.' });
    }

    const beneficiaryResult = await pool.query(
      'SELECT * FROM beneficiaries WHERE id = $1 AND user_id = $2',
      [beneficiary_id, userId]
    );
    if (beneficiaryResult.rows.length === 0) {
      return res.status(404).json({ message: 'Beneficiary not found.' });
    }
    const beneficiary = beneficiaryResult.rows[0];

    // Simulate RazorpayX payout (in real, call RazorpayX API here)
    // For now, just deduct and add transaction
    const newBalance = parseFloat(account.balance) - parseFloat(amount);
    await pool.query(
      'UPDATE accounts SET balance = $1 WHERE id = $2',
      [newBalance, account.id]
    );
    await pool.query(
      `INSERT INTO transactions (user_id, type, amount, to_account, status, reference_id)
       VALUES ($1, $2, $3, $4, $5, $6)`,
      [userId, 'debit', amount, beneficiary.account_number, 'success', 'simulated_ref']
    );

    res.json({ message: 'Transfer successful.', newBalance });
  } catch (err) {
    console.error('Transfer error:', err);
    res.status(500).json({ message: 'Transfer failed.' });
  }
};

// 6b. Secure Transfer with Biometric Authentication (REPLACES PIN-based transfer)
exports.secureTransfer = async (req, res) => {
  const userId = req.userId;
  const { amount, beneficiary_id, videoFrames } = req.body;

  console.log('🔐 Secure biometric transfer initiated for user ID:', userId);

  // Input validation
  if (!beneficiary_id || isNaN(Number(beneficiary_id))) {
    return res.status(400).json({ message: 'Valid beneficiary is required.' });
  }
  if (!amount || isNaN(Number(amount)) || Number(amount) <= 0) {
    return res.status(400).json({ message: 'Amount must be a positive number.' });
  }
  if (!videoFrames || !Array.isArray(videoFrames)) {
    return res.status(400).json({ message: 'Video frames required for biometric authentication.' });
  }
  if (videoFrames.length < 20) {
    return res.status(400).json({ message: 'Insufficient frames. Please provide at least 20 frames.' });
  }

  try {
    // Step 1: Check if user has enrolled biometrics
    const userCheck = await pool.query(
      'SELECT id, username, face_biometric, hand_biometric, style_biometric FROM users WHERE id = $1',
      [userId]
    );
    
    if (userCheck.rows.length === 0) {
      return res.status(404).json({ message: 'User not found.' });
    }

    const user = userCheck.rows[0];
    
    // Check if user has enrolled biometrics for transfer authentication
    // NOTE: face_biometric is for face login, NOT for transfer auth
    // Transfer auth uses hand_biometric and style_biometric as enrollment markers
    if (!user.hand_biometric || !user.style_biometric) {
      return res.status(403).json({ 
        message: 'Biometric authentication not enrolled. Please enroll your biometrics via dashboard first.',
        enrollmentRequired: true
      });
    }

    console.log(`✅ User ${user.username} has biometrics enrolled for transfer authentication`);

    // Step 2: Convert base64 frames to Buffers
    const frameBuffers = biometricService.base64ArrayToBuffers(videoFrames);
    console.log(`📹 Converted ${frameBuffers.length} frames for verification`);

    // Step 3: Verify biometrics using NS-AGF (REAL FUSION: face + hand + style)
    let verificationResult;
    try {
      verificationResult = await biometricService.verifyBiometrics(frameBuffers, userId);
    } catch (verifyErr) {
      console.error('❌ Biometric verification error:', verifyErr.message);
      
      // Check if NS-AGF service is not running
      if (verifyErr.message.includes('ECONNREFUSED') || verifyErr.message.includes('not running')) {
        return res.status(503).json({ 
          message: 'Biometric verification service unavailable',
          details: 'NS-AGF API is not running. Please start: python ns_agf/api_service.py',
          serviceRequired: true
        });
      }
      
      // Log failed authentication attempt
      await pool.query(
        `INSERT INTO biometric_auth_log 
         (user_id, auth_type, face_score, hand_score, style_score, fusion_score, authenticated, ip_address, user_agent)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`,
        [userId, 'transfer', 0, 0, 0, 0, false, req.ip, req.headers['user-agent']]
      );

      return res.status(500).json({ 
        message: 'Biometric verification failed',
        details: verifyErr.message
      });
    }

    // Extract scores from NS-AGF response
    const authenticated = verificationResult.authenticated;
    const faceScore = verificationResult.faceScore;
    const handScore = verificationResult.handScore;
    const styleScore = verificationResult.styleScore;
    const fusionScore = verificationResult.fusionScore;

    console.log('🔍 Biometric scores (NS-AGF Fusion):');
    console.log(`   👤 Face: ${faceScore.toFixed(3)}`);
    console.log(`   ✋ Hand: ${handScore.toFixed(3)}`);
    console.log(`   ✍️  Style: ${styleScore.toFixed(3)}`);
    console.log(`   🔗 Fusion: ${fusionScore.toFixed(3)}`);

    // Step 4: Check if authentication passed (threshold: 0.65)
    if (!authenticated || fusionScore < 0.65) {
      console.error('❌ Authentication failed - fusion score below threshold:', fusionScore);
      
      // Log failed authentication with scores
      await pool.query(
        `INSERT INTO biometric_auth_log 
         (user_id, auth_type, face_score, hand_score, style_score, fusion_score, authenticated, ip_address, user_agent)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`,
        [userId, 'transfer', faceScore, handScore, styleScore, fusionScore, false, req.ip, req.headers['user-agent']]
      );

      return res.status(401).json({ 
        message: 'Biometric authentication failed - insufficient match',
        scores: { faceScore, handScore, styleScore, fusionScore },
        threshold: 0.65
      });
    }

    console.log('✅ Biometric authentication successful! (Face + Hand + Style Fusion)');

    // Step 5: Get user account and beneficiary
    const accountResult = await pool.query(
      'SELECT id, balance, account_number FROM accounts WHERE user_id = $1',
      [userId]
    );
    if (accountResult.rows.length === 0) {
      return res.status(404).json({ message: 'Account not found.' });
    }
    const account = accountResult.rows[0];

    if (parseFloat(account.balance) < parseFloat(amount)) {
      return res.status(400).json({ message: 'Insufficient balance.' });
    }

    const beneficiaryResult = await pool.query(
      'SELECT * FROM beneficiaries WHERE id = $1 AND user_id = $2',
      [beneficiary_id, userId]
    );
    if (beneficiaryResult.rows.length === 0) {
      return res.status(404).json({ message: 'Beneficiary not found.' });
    }
    const beneficiary = beneficiaryResult.rows[0];

    // Step 6: Process transfer (in transaction)
    const client = await pool.connect();
    
    try {
      await client.query('BEGIN');

      // Deduct from sender
      const newBalance = parseFloat(account.balance) - parseFloat(amount);
      await client.query(
        'UPDATE accounts SET balance = $1 WHERE id = $2',
        [newBalance, account.id]
      );

      // Insert transaction record
      const transactionResult = await client.query(
        `INSERT INTO transactions (user_id, type, amount, to_account, status, reference_id)
         VALUES ($1, $2, $3, $4, $5, $6) RETURNING id`,
        [userId, 'debit', amount, beneficiary.account_number, 'success', `bio_${Date.now()}`]
      );
      
      const transactionId = transactionResult.rows[0].id;

      // Log successful biometric authentication with transaction link
      await client.query(
        `INSERT INTO biometric_auth_log 
         (user_id, auth_type, face_score, hand_score, style_score, fusion_score, authenticated, transaction_id, ip_address, user_agent)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)`,
        [userId, 'transfer', faceScore, handScore, styleScore, fusionScore, true, transactionId, req.ip, req.headers['user-agent']]
      );

      await client.query('COMMIT');

      console.log(`✅ Transfer successful: ${amount} to ${beneficiary.name} (Account: ${beneficiary.account_number})`);

      res.json({ 
        success: true,
        message: 'Transfer completed successfully with biometric authentication',
        data: {
          transactionId,
          amount,
          beneficiary: beneficiary.name,
          newBalance,
          biometricScores: {
            face: faceScore,
            hand: handScore,
            style: styleScore,
            fusion: fusionScore
          }
        }
      });

    } catch (transactionErr) {
      await client.query('ROLLBACK');
      console.error('❌ Transaction error:', transactionErr);
      throw transactionErr;
    } finally {
      client.release();
    }

  } catch (err) {
    console.error('Secure transfer error:', err);
    
    // Handle specific errors
    if (err.message && err.message.includes('ECONNREFUSED')) {
      return res.status(503).json({ 
        message: 'Biometric service unavailable',
        details: 'NS-AGF API service is not running. Please contact support.'
      });
    }

    if (err.message && err.message.includes('User not enrolled')) {
      return res.status(404).json({ 
        message: 'Biometric authentication failed',
        details: 'User biometrics not found in verification service'
      });
    }

    res.status(500).json({ 
      message: 'Transfer failed', 
      details: err.message 
    });
  }
};

// 7. Transaction History
exports.getHistory = async (req, res) => {
  const userId = req.userId;
  try {
    const result = await pool.query(
      `SELECT type, amount, to_account, status, reference_id, timestamp
       FROM transactions WHERE user_id = $1
       ORDER BY timestamp DESC LIMIT 20`,
      [userId]
    );
    res.json(result.rows);
  } catch (err) {
    console.error('Get history error:', err);
    res.status(500).json({ message: 'Failed to fetch history.' });
  }
};

// Razorpay Order Creation (for payments)

exports.createOrder = async (req, res) => {
  const { amount } = req.body; // amount in INR
  try {
    const order = await razorpay.orders.create({
      amount: amount * 100, // Razorpay expects amount in paise
      currency: "INR",
      receipt: `receipt_${Date.now()}`
    });
    res.json(order);
  } catch (err) {
    console.error('Create order error:', err);
    res.status(500).json({ message: 'Failed to create order.' });
  }
};

//8 Razorpay payment verification and wallet update
exports.verifyAndAddMoney = async (req, res) => {
  const { razorpay_payment_id, razorpay_order_id, amount } = req.body;
  const userId = req.userId;

  // (Optional) Verify payment with Razorpay API
  // For demo, we'll trust the frontend in test mode
  try {
    // Update user's wallet balance
    const accountResult = await pool.query(
      'SELECT id, balance FROM accounts WHERE user_id = $1',
      [userId]
    );
    if (accountResult.rows.length === 0) {
      return res.status(404).json({ message: 'Account not found.' });
    }
    const account = accountResult.rows[0];
    const newBalance = parseFloat(account.balance) + parseFloat(amount);

    await pool.query(
      'UPDATE accounts SET balance = $1 WHERE id = $2',
      [newBalance, account.id]
    );

    // Record transaction
    await pool.query(
      `INSERT INTO transactions (user_id, type, amount, to_account, status, reference_id)
       VALUES ($1, $2, $3, $4, $5, $6)`,
      [userId, 'credit', amount, account.id, 'success', razorpay_payment_id]
    );

    res.json({ message: 'Wallet updated', newBalance });
  } catch (err) {
    console.error('Add money error:', err);
    res.status(500).json({ message: 'Failed to update wallet.' });
  }
};