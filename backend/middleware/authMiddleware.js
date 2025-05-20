const jwt = require('jsonwebtoken');
require('dotenv').config();

const authMiddleware = (req, res, next) => {
    try {
        const token = req.headers.authorization?.split(' ')[1];
        console.log('Auth check - Token received:', token ? 'Yes' : 'No');

        if (!token) {
            return res.status(401).json({ message: 'No token provided' });
        }

        const decoded = jwt.verify(token, process.env.JWT_SECRET);
        req.userId = decoded.id; // Change from req.user to req.userId to match your userController
        console.log('Token verified for user ID:', decoded.id);
        next();
    } catch (err) {
        console.error('Token verification failed:', err.message);
        res.status(401).json({ message: 'Invalid token' });
    }
};

module.exports = authMiddleware;