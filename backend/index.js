const express = require('express');
const multer = require('multer');
const cors = require('cors');
const dotenv = require('dotenv');
const { registerFace, loginFace, registerVoice, loginVoice,getUserData,getLoginHistory,logout } = require('./controllers/userController');
const path = require('path');
const authMiddleware = require('./middleware/authMiddleware');

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


// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: err.message });
});

// Start server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Backend running on port ${PORT}`));
