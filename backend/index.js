const express = require('express');
const multer = require('multer');
const cors = require('cors');
const dotenv = require('dotenv');
const { registerFace, loginFace, registerVoice, loginVoice,getUserData,getLoginHistory,logout,sendOtp,verifyOtp } = require('./controllers/userController');
const path = require('path');
const authMiddleware = require('./middleware/authMiddleware');

const razorpay = require('./razorpay'); // Add this line
const bankController = require('./controllers/bankController');
const crypto = require('crypto');
const rateLimit = require('express-rate-limit');
const { body, validationResult } = require('express-validator');

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'uploads/');
  },
  filename: (req, file, cb) => {
    cb(null, Date.now() + path.extname(file.originalname));
  }
});

const upload = multer({ storage });

const fs = require('fs');
if (!fs.existsSync('uploads')) {
  fs.mkdirSync('uploads');
}

// ========= Face Auth Routes ========= //
app.post('/api/register', upload.single('image'), registerFace);
app.post('/api/login', upload.single('image'), loginFace);

// ========= Voice Auth Routes ========= //
app.post('/api/voice/register', upload.single('audio'), registerVoice);
app.post('/api/voice/login', upload.single('audio'), loginVoice);



// Protected routes
app.get('/api/user', authMiddleware,getUserData);
app.get('/api/login-history', authMiddleware,getLoginHistory);
app.post('/api/logout', authMiddleware,logout);


// Razorpay test route
app.get('/api/razorpay/test', async (req, res) => {
  try {
    // This will fail but proves SDK is working and keys are loaded
    await razorpay.payments.all({ count: 1 });
    res.json({ message: 'Razorpay SDK initialized and test call succeeded!' });
  } catch (err) {
    res.json({ message: 'Razorpay SDK initialized!', error: err.message });
  }
});



// PIN management
app.post('/api/account/set-pin', authMiddleware, bankController.setPin);
app.post('/api/account/verify-pin', authMiddleware, bankController.verifyPin);

// Balance
app.get('/api/account/balance', authMiddleware, bankController.getBalance);

// Beneficiaries
app.post('/api/account/beneficiaries', authMiddleware, bankController.addBeneficiary);
app.get('/api/account/beneficiaries', authMiddleware, bankController.listBeneficiaries);

// Transfer
app.post('/api/account/transfer', authMiddleware, bankController.transfer);

// Transaction History
app.get('/api/account/history', authMiddleware, bankController.getHistory);


// Razorpay Order Creation
app.post('/api/razorpay/order', authMiddleware, bankController.createOrder);

// Razorpay Webhook Endpoint
app.post('/api/webhook/razorpay', express.json({ verify: (req, res, buf) => { req.rawBody = buf } }), async (req, res) => {
  const secret = process.env.RAZORPAY_WEBHOOK_SECRET;
  const signature = req.headers['x-razorpay-signature'];

  // Verify webhook signature
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(req.rawBody)
    .digest('hex');

  if (signature !== expectedSignature) {
    return res.status(400).json({ message: 'Invalid signature' });
  }

  // Process webhook event
  const event = req.body.event;
  const payload = req.body.payload;

  // Example: handle payout status update
  if (event === 'payout.processed' || event === 'payout.failed') {
    const payoutId = payload.payout.entity.id;
    const status = payload.payout.entity.status; // 'processed', 'failed', etc.

    // Update your transactions table with the new status
    try {
      await pool.query(
        'UPDATE transactions SET status = $1 WHERE reference_id = $2',
        [status, payoutId]
      );
    } catch (err) {
      console.error('Webhook DB update error:', err);
    }
  }

  res.json({ status: 'ok' });
});



// Apply rate limiting to sensitive routes (e.g., PIN verify, transfer)
const pinLimiter = rateLimit({
  windowMs: 5 * 60 * 1000, // 5 minutes
  max: 5, // limit each IP to 5 requests per windowMs
  message: { message: 'Too many attempts, please try again later.' }
});

app.post('/api/account/verify-pin', pinLimiter, bankController.verifyPin);
app.post('/api/account/transfer', pinLimiter, bankController.transfer);




app.post(
  '/api/account/beneficiaries',
  [
    authMiddleware,
    body('name').isString().isLength({ min: 2 }),
    body('account_number').matches(/^\d{9,18}$/),
    body('ifsc').matches(/^[A-Z]{4}0[A-Z0-9]{6}$/)
  ],
  (req, res, next) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ message: 'Validation failed', errors: errors.array() });
    }
    next();
  },
  bankController.addBeneficiary
);

//wallet add money
app.post('/api/razorpay/verify', authMiddleware, bankController.verifyAndAddMoney);

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);
  res.status(500).json({ message: 'Internal server error.' });
});

// OTP Auth Routes
app.post('/api/otp/send', sendOtp);
app.post('/api/otp/verify', verifyOtp);

// Start server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Backend running on port ${PORT}`));

