const nodemailer = require('nodemailer');

const transporter = nodemailer.createTransport({
  service: 'gmail',
  auth: {
    user: process.env.EMAIL_USER,
    pass: process.env.EMAIL_APP_PASSWORD // Use App Password from Gmail
  }
});

const sendOTP = async (email, otp) => {
  const mailOptions = {
    from: process.env.EMAIL_USER,
    to: email,
    subject: 'Authentication OTP',
    html: `
      <div style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
        <h2 style="color: #333;">Your Authentication OTP</h2>
        <p>Please use the following OTP to verify your account:</p>
        <h1 style="color: #4CAF50; font-size: 32px;">${otp}</h1>
        <p>This OTP will expire in 5 minutes.</p>
        <p>If you didn't request this OTP, please ignore this email.</p>
      </div>
    `
  };

  try {
    await transporter.sendMail(mailOptions);
    return true;
  } catch (error) {
    console.error('Email sending failed:', error);
    return false;
  }
};

module.exports = { sendOTP };