const express = require('express');
const multer = require('multer');
const cors = require('cors');
const dotenv = require('dotenv');
const { registerUser, loginUser } = require('./controllers/userController');

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

const upload = multer({ dest: 'uploads/' });

app.post('/api/register', upload.single('image'), registerUser);
app.post('/api/login', upload.single('image'), loginUser);

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Backend running on port ${PORT}`));
