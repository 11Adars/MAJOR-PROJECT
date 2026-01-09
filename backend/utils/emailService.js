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

// Send support query to bank email
const sendQueryToBank = async (userEmail, userName, queryText, ticketId) => {
  const bankEmail = process.env.BANK_SUPPORT_EMAIL || process.env.EMAIL_USER;
  
  console.log(`[emailService] sendQueryToBank called`);
  console.log(`  - Bank email: ${bankEmail}`);
  console.log(`  - User: ${userName} (${userEmail})`);
  console.log(`  - Ticket: #${ticketId}`);
  
  const mailOptions = {
    from: process.env.EMAIL_USER,
    to: bankEmail,
    replyTo: userEmail,
    subject: `Support Query #${ticketId} from ${userName}`,
    html: `
      <div style="font-family: Arial, sans-serif; padding: 20px; background-color: #f9f9f9;">
        <div style="background-color: #667eea; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
          <h2 style="margin: 0;">🤟 New Customer Support Query</h2>
          <p style="margin: 5px 0 0 0; opacity: 0.9;">Generated via Sign Language Recognition</p>
        </div>
        
        <div style="background-color: white; padding: 20px; border: 1px solid #e0e0e0; border-radius: 0 0 8px 8px;">
          <h3 style="color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px;">Ticket Details</h3>
          
          <table style="width: 100%; margin: 20px 0;">
            <tr>
              <td style="padding: 8px; background-color: #f5f5f5; font-weight: bold; width: 150px;">Ticket ID:</td>
              <td style="padding: 8px;">#${ticketId}</td>
            </tr>
            <tr>
              <td style="padding: 8px; background-color: #f5f5f5; font-weight: bold;">Customer Name:</td>
              <td style="padding: 8px;">${userName}</td>
            </tr>
            <tr>
              <td style="padding: 8px; background-color: #f5f5f5; font-weight: bold;">Customer Email:</td>
              <td style="padding: 8px;"><a href="mailto:${userEmail}">${userEmail}</a></td>
            </tr>
            <tr>
              <td style="padding: 8px; background-color: #f5f5f5; font-weight: bold;">Query Source:</td>
              <td style="padding: 8px;">Sign Language Recognition</td>
            </tr>
          </table>
          
          <h3 style="color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px;">Customer Query</h3>
          <div style="background-color: #f0f4ff; padding: 15px; border-left: 4px solid #667eea; margin: 15px 0;">
            <p style="font-size: 16px; line-height: 1.6; margin: 0;">${queryText}</p>
          </div>
          
          <div style="margin-top: 30px; padding: 15px; background-color: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;">
            <p style="margin: 0; font-weight: bold; color: #856404;">📧 How to Respond:</p>
            <p style="margin: 5px 0 0 0; color: #856404;">Simply reply to this email. Your response will automatically be sent to the customer and displayed in their dashboard.</p>
          </div>
        </div>
        
        <div style="margin-top: 20px; padding: 15px; background-color: #f5f5f5; border-radius: 8px; font-size: 12px; color: #666;">
          <p style="margin: 0;">BankAssist AI - Customer Support System</p>
          <p style="margin: 5px 0 0 0;">This email was generated automatically from a sign language query.</p>
        </div>
      </div>
    `
  };

  try {
    console.log(`[emailService] Sending email via nodemailer...`);
    const info = await transporter.sendMail(mailOptions);
    console.log(`[emailService] ✅ Email sent successfully!`);
    console.log(`  - MessageId: ${info.messageId}`);
    console.log(`  - Response: ${info.response}`);
    return true;
  } catch (error) {
    console.error('[emailService] ❌ Failed to send query to bank:');
    console.error(`  - Error: ${error.message}`);
    console.error(`  - Code: ${error.code}`);
    if (error.response) {
      console.error(`  - SMTP Response: ${error.response}`);
    }
    return false;
  }
};

// Send confirmation to user that their query was submitted
const sendQueryConfirmation = async (userEmail, userName, queryText, ticketId) => {
  console.log(`[emailService] sendQueryConfirmation called`);
  console.log(`  - To: ${userName} (${userEmail})`);
  console.log(`  - Ticket: #${ticketId}`);
  
  const mailOptions = {
    from: process.env.EMAIL_USER,
    to: userEmail,
    subject: `Support Query Submitted - Ticket #${ticketId}`,
    html: `
      <div style="font-family: Arial, sans-serif; padding: 20px; background-color: #f9f9f9;">
        <div style="background-color: #10b981; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
          <h2 style="margin: 0;">✅ Query Submitted Successfully</h2>
          <p style="margin: 5px 0 0 0; opacity: 0.9;">We've received your support request</p>
        </div>
        
        <div style="background-color: white; padding: 20px; border: 1px solid #e0e0e0; border-radius: 0 0 8px 8px;">
          <p style="font-size: 16px; color: #333;">Hi ${userName},</p>
          
          <p style="font-size: 14px; color: #666; line-height: 1.6;">
            Thank you for contacting BankAssist AI support. Your query has been successfully submitted and forwarded to our support team.
          </p>
          
          <div style="background-color: #f0f4ff; padding: 15px; border-left: 4px solid #667eea; margin: 20px 0;">
            <p style="margin: 0; font-weight: bold; color: #667eea;">Your Ticket ID: #${ticketId}</p>
            <p style="margin: 10px 0 0 0; color: #555; font-size: 14px;">Keep this ID for your reference.</p>
          </div>
          
          <h3 style="color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px;">Your Query</h3>
          <div style="background-color: #f5f5f5; padding: 15px; border-radius: 4px; margin: 15px 0;">
            <p style="font-size: 14px; line-height: 1.6; margin: 0; color: #333;">${queryText}</p>
          </div>
          
          <div style="margin-top: 20px; padding: 15px; background-color: #e7f3ff; border-left: 4px solid #2196F3; border-radius: 4px;">
            <p style="margin: 0; font-weight: bold; color: #1976D2;">📱 Track Your Query</p>
            <p style="margin: 5px 0 0 0; color: #1976D2; font-size: 14px;">
              You can track the status of your query in your dashboard. We'll notify you via email when our team responds.
            </p>
          </div>
          
          <p style="margin-top: 30px; font-size: 14px; color: #666;">
            Our support team typically responds within 24 hours. You'll receive an email notification and the response will appear in your dashboard.
          </p>
        </div>
        
        <div style="margin-top: 20px; padding: 15px; background-color: #f5f5f5; border-radius: 8px; font-size: 12px; color: #666; text-align: center;">
          <p style="margin: 0;">BankAssist AI - Customer Support</p>
          <p style="margin: 5px 0 0 0;">Need immediate assistance? Contact us at ${process.env.BANK_SUPPORT_EMAIL || 'support@bankassist.ai'}</p>
        </div>
      </div>
    `
  };

  try {
    console.log(`[emailService] Sending confirmation email via nodemailer...`);
    const info = await transporter.sendMail(mailOptions);
    console.log(`[emailService] ✅ Confirmation email sent successfully!`);
    console.log(`  - MessageId: ${info.messageId}`);
    console.log(`  - Response: ${info.response}`);
    return true;
  } catch (error) {
    console.error('[emailService] ❌ Failed to send confirmation to user:');
    console.error(`  - Error: ${error.message}`);
    console.error(`  - Code: ${error.code}`);
    if (error.response) {
      console.error(`  - SMTP Response: ${error.response}`);
    }
    return false;
  }
};

// Notify user when bank responds to their query
const notifyUserOfResponse = async (userEmail, userName, queryText, responseText, ticketId) => {
  const mailOptions = {
    from: process.env.EMAIL_USER,
    to: userEmail,
    subject: `Response Received - Ticket #${ticketId}`,
    html: `
      <div style="font-family: Arial, sans-serif; padding: 20px; background-color: #f9f9f9;">
        <div style="background-color: #667eea; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
          <h2 style="margin: 0;">💬 New Response to Your Query</h2>
          <p style="margin: 5px 0 0 0; opacity: 0.9;">Our support team has responded</p>
        </div>
        
        <div style="background-color: white; padding: 20px; border: 1px solid #e0e0e0; border-radius: 0 0 8px 8px;">
          <p style="font-size: 16px; color: #333;">Hi ${userName},</p>
          
          <p style="font-size: 14px; color: #666; line-height: 1.6;">
            Great news! Our support team has responded to your query (Ticket #${ticketId}).
          </p>
          
          <h3 style="color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px;">Your Original Query</h3>
          <div style="background-color: #f5f5f5; padding: 15px; border-radius: 4px; margin: 15px 0;">
            <p style="font-size: 14px; line-height: 1.6; margin: 0; color: #666;">${queryText}</p>
          </div>
          
          <h3 style="color: #333; border-bottom: 2px solid #10b981; padding-bottom: 10px;">Support Team Response</h3>
          <div style="background-color: #ecfdf5; padding: 15px; border-left: 4px solid #10b981; margin: 15px 0;">
            <p style="font-size: 14px; line-height: 1.6; margin: 0; color: #333;">${responseText}</p>
          </div>
          
          <div style="margin-top: 20px; padding: 15px; background-color: #e7f3ff; border-left: 4px solid #2196F3; border-radius: 4px;">
            <p style="margin: 0; font-weight: bold; color: #1976D2;">📱 View in Dashboard</p>
            <p style="margin: 5px 0 0 0; color: #1976D2; font-size: 14px;">
              This response is also available in your dashboard. Login to view all your support tickets and responses.
            </p>
          </div>
          
          <p style="margin-top: 30px; font-size: 14px; color: #666;">
            If you need further assistance with this query, please reply to this email or create a new support ticket.
          </p>
        </div>
        
        <div style="margin-top: 20px; padding: 15px; background-color: #f5f5f5; border-radius: 8px; font-size: 12px; color: #666; text-align: center;">
          <p style="margin: 0;">BankAssist AI - Customer Support</p>
          <p style="margin: 5px 0 0 0;">Thank you for using our services!</p>
        </div>
      </div>
    `
  };

  try {
    await transporter.sendMail(mailOptions);
    return true;
  } catch (error) {
    console.error('Failed to notify user of response:', error);
    return false;
  }
};

module.exports = { 
  sendOTP, 
  sendQueryToBank, 
  sendQueryConfirmation,
  notifyUserOfResponse
};