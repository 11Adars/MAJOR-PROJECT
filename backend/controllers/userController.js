const pool = require('../db');
const jwt = require('jsonwebtoken');
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

const generateToken = (id) =>
  jwt.sign({ id }, process.env.JWT_SECRET, { expiresIn: '1h' });

exports.registerUser = async (req, res) => {
  const { username, email } = req.body;
  const image = req.file.path;

  const form = new FormData();
  form.append('image', fs.createReadStream(image));

  const { data } = await axios.post(process.env.PYTHON_SERVICE_URL, form, {
    headers: form.getHeaders(),
  });

  const embedding = data.embedding;

  const result = await pool.query(
    'INSERT INTO users (username, email, face_embedding) VALUES ($1, $2, $3) RETURNING id',
    [username, email, embedding]
  );

  const token = generateToken(result.rows[0].id);
  res.json({ success: true, token });
};

exports.loginUser = async (req, res) => {
  const { username } = req.body;
  const image = req.file.path;

  const userResult = await pool.query(
    'SELECT * FROM users WHERE username = $1',
    [username]
  );

  if (userResult.rows.length === 0)
    return res.status(404).json({ error: 'User not found' });

  const savedEmbedding = userResult.rows[0].face_embedding;

  const form = new FormData();
  form.append('image', fs.createReadStream(image));

  const { data } = await axios.post(process.env.PYTHON_SERVICE_URL, form, {
    headers: form.getHeaders(),
  });

  const loginEmbedding = data.embedding;

  // Cosine similarity
  const dot = loginEmbedding.reduce((sum, val, i) => sum + val * savedEmbedding[i], 0);
  const normA = Math.sqrt(savedEmbedding.reduce((sum, val) => sum + val * val, 0));
  const normB = Math.sqrt(loginEmbedding.reduce((sum, val) => sum + val * val, 0));
  const similarity = dot / (normA * normB);

  if (similarity > 0.5) {
    const token = generateToken(userResult.rows[0].id);
    res.json({ success: true, token });
  } else {
    res.status(401).json({ error: 'Face authentication failed' });
  }
};
