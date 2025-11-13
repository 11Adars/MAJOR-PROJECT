# Support Ticket System Setup Guide

## Overview
This guide will help you set up the complete email-based support ticket system where sign language queries are sent to a bank email, and bank responses appear in the user's dashboard.

---

## 📋 Prerequisites

1. **Gmail Account**: You need at least 1 Gmail account for the bank support email
2. **PostgreSQL Database**: Already configured in your project
3. **Gmail App Password**: You'll need to generate an app-specific password for Gmail SMTP

---

## 🔧 Step 1: Configure Gmail App Password

### Why App Password?
Gmail requires app-specific passwords for third-party applications using SMTP.

### Steps to Generate:

1. Go to your Google Account: https://myaccount.google.com/
2. Navigate to **Security** > **2-Step Verification** (enable if not already enabled)
3. Scroll down to **App passwords**
4. Click **Select app** and choose **Mail**
5. Click **Select device** and choose **Other (Custom name)**
6. Enter "BankAssist AI" and click **Generate**
7. **Copy the 16-character password** (you'll need this in Step 3)

---

## 🗄️ Step 2: Set Up Database Tables

### Execute the SQL Schema

1. **Open PostgreSQL Client** (pgAdmin, psql, or your preferred tool)
2. **Connect to your database** (the same one used by your Node.js backend)
3. **Run the schema file**:

```bash
# Using psql command line:
psql -U your_username -d your_database_name -f backend/database_schema_tickets.sql

# Or in pgAdmin:
# - Open Query Tool
# - Open file: backend/database_schema_tickets.sql
# - Execute (F5)
```

### Verify Tables Created

Run this query to confirm:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('support_tickets', 'ticket_responses');
```

You should see both tables listed.

---

## ⚙️ Step 3: Configure Backend Environment

### Update `.env` File

Edit `backend/.env` and add/update these variables:

```env
# Email Configuration
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-16-char-app-password

# Bank Support Email (where queries are sent)
BANK_SUPPORT_EMAIL=your-bank-support-email@gmail.com

# Optional: Customize email settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
```

### Example Configuration

If you have 3 Gmail accounts:
- `user1@gmail.com` - Your personal email
- `bankassist@gmail.com` - For sending emails (set as EMAIL_USER)
- `banksupport@gmail.com` - Bank support inbox (set as BANK_SUPPORT_EMAIL)

```env
EMAIL_USER=bankassist@gmail.com
EMAIL_PASS=abcd efgh ijkl mnop
BANK_SUPPORT_EMAIL=banksupport@gmail.com
```

> **Note**: Use the same email for both if you only have one Gmail account.

---

## 📦 Step 4: Install Dependencies

Make sure all required packages are installed:

```bash
# Backend dependencies (if not already installed)
cd backend
npm install nodemailer

# Sign service dependencies
cd ../Sign
pip install requests==2.31.0

# Frontend dependencies
cd ../frontend
npm install axios react-router-dom react-icons
```

---

## 🚀 Step 5: Start All Services

### Start Backend Server

```bash
cd backend
node index.js
```

Expected output:
```
Server running on port 5000
Database connected
```

### Start Sign Recognition Service

```bash
# Windows
cd Sign
start_service.bat

# Linux/Mac
cd Sign
chmod +x start_service.sh
./start_service.sh
```

Expected output:
```
Loading sign language model...
Starting Flask server on http://127.0.0.1:8000
```

### Start Frontend

```bash
cd frontend
npm start
```

Expected output:
```
Compiled successfully!
You can now view frontend in the browser.
Local: http://localhost:3000
```

---

## 🧪 Step 6: Test the Complete Flow

### Test 1: Submit a Sign Language Query

1. **Login to the application**: http://localhost:3000/login
2. **Navigate to Dashboard**: Click "Customer Support" in Quick Actions
3. **Record Sign Language**:
   - Allow camera access
   - Click "Start Recording"
   - Perform sign language gestures
   - Click "Stop Recording"
4. **Generate Query**: Click "Generate Sentence"
5. **Submit to Bank**: Click "Submit to Bank Support"
6. **Verify Success**: You should see a success message with a ticket ID

### Test 2: Check Bank Email

1. **Open the bank support Gmail**: Check `BANK_SUPPORT_EMAIL` inbox
2. **Verify email received**:
   - Subject: "New Support Query from [Username] - Ticket #[ID]"
   - Contains the generated query text
   - Has user's email address for replies

### Test 3: Reply as Bank Admin

1. **In the bank email**, click "Reply" on the support query email
2. **Write a response** to the user's query
3. **Send the email** to the user's email address

### Test 4: Check User Dashboard

1. **Navigate to Support Tickets**: http://localhost:3000/support-tickets
   - Or click "Support Tickets" in Quick Actions
2. **Verify ticket appears** in the list
3. **Click on the ticket** to view details
4. **Check for bank response**: Should appear in the responses section
5. **Mark as Resolved**: Click "Mark as Resolved" when done

---

## 📊 Understanding the Ticket System

### Ticket Statuses

| Status | Description |
|--------|-------------|
| `pending` | Initial state when ticket is created |
| `responded` | Bank has replied to the query |
| `resolved` | User has marked the ticket as resolved |

### Ticket Source Types

| Source | Description |
|--------|-------------|
| `sign_language` | Queries from sign recognition service |
| `manual` | Future: Manual ticket creation |
| `email` | Future: Direct email submissions |

### Email Flow Diagram

```
User Sign Query → Sign Service → Backend API
                                     ↓
                              Create Ticket in DB
                                     ↓
                         Send Email to Bank Support
                                     ↓
                         Send Confirmation to User
                                     ↓
                         Bank Replies to User Email
                                     ↓
                         Webhook/Manual Entry in DB
                                     ↓
                         User Views Response in Dashboard
```

---

## 🔍 Troubleshooting

### Problem: "Authentication failed" when sending email

**Solution**:
1. Verify app password is correct (16 characters, no spaces)
2. Ensure 2-Step Verification is enabled on Gmail
3. Check EMAIL_USER and EMAIL_PASS in `.env`
4. Try generating a new app password

### Problem: Tickets not appearing in dashboard

**Solution**:
1. Check database tables exist:
   ```sql
   SELECT * FROM support_tickets;
   ```
2. Verify backend API is running on port 5000
3. Check browser console for errors (F12)
4. Ensure user is logged in (token in localStorage)

### Problem: Sign service can't connect to backend

**Solution**:
1. Verify backend is running on port 5000
2. Check Sign/sign_service.py has correct backend URL:
   ```python
   backend_url = 'http://127.0.0.1:5000'
   ```
3. Ensure `requests` library is installed:
   ```bash
   pip install requests==2.31.0
   ```

### Problem: Bank email not received

**Solution**:
1. Check spam folder in bank support email
2. Verify BANK_SUPPORT_EMAIL is set correctly in `.env`
3. Check backend logs for email sending errors
4. Test email configuration:
   ```javascript
   // backend/utils/emailService.js
   // Add console.log to see email status
   ```

---

## 📝 Manual Testing Commands

### Check Database Records

```sql
-- View all tickets
SELECT * FROM support_tickets ORDER BY created_at DESC;

-- View tickets with responses
SELECT 
  t.id, 
  t.query_text, 
  t.status, 
  COUNT(r.id) as response_count
FROM support_tickets t
LEFT JOIN ticket_responses r ON t.id = r.ticket_id
GROUP BY t.id, t.query_text, t.status;

-- View all responses
SELECT * FROM ticket_responses ORDER BY created_at DESC;
```

### Test Backend API Endpoints

```bash
# Get user's tickets (replace TOKEN with your JWT)
curl -H "Authorization: Bearer TOKEN" http://localhost:5000/api/support/tickets

# Get ticket details
curl -H "Authorization: Bearer TOKEN" http://localhost:5000/api/support/tickets/1

# Get support stats
curl -H "Authorization: Bearer TOKEN" http://localhost:5000/api/support/stats
```

---

## 🎯 Next Steps

### For Development:

1. **Bank Admin Interface**: Create a separate admin portal for bank staff to view and respond to tickets
2. **Email Webhook**: Set up automatic email parsing to capture bank responses
3. **Notifications**: Add real-time notifications when bank responds
4. **File Attachments**: Allow users to attach images/documents to queries
5. **Chat Integration**: Add real-time chat for urgent queries

### For Production:

1. **Configure Production Email**: Use professional email service (SendGrid, AWS SES)
2. **Set up HTTPS**: Ensure all communications are encrypted
3. **Add Rate Limiting**: Prevent spam/abuse
4. **Set up Monitoring**: Track email delivery, response times
5. **Backup Database**: Regular backups of support tickets

---

## 📞 Support

If you encounter any issues:

1. Check the logs:
   - Backend: Console output where you ran `node index.js`
   - Sign Service: Console output where you ran `start_service.bat`
   - Frontend: Browser console (F12 → Console tab)

2. Verify all services are running:
   - Backend: http://localhost:5000
   - Sign Service: http://localhost:8000
   - Frontend: http://localhost:3000

3. Check database connectivity:
   ```bash
   # Test PostgreSQL connection
   psql -U your_username -d your_database_name -c "SELECT version();"
   ```

---

## ✅ Completion Checklist

- [ ] Gmail app password generated
- [ ] Database tables created (support_tickets, ticket_responses)
- [ ] Backend .env configured (EMAIL_USER, EMAIL_PASS, BANK_SUPPORT_EMAIL)
- [ ] All dependencies installed
- [ ] Backend server running (port 5000)
- [ ] Sign service running (port 8000)
- [ ] Frontend running (port 3000)
- [ ] Test query submitted successfully
- [ ] Bank email received
- [ ] Ticket visible in dashboard
- [ ] Bank reply flow tested

---

## 🎉 Success!

Once all steps are complete, your support ticket system is fully operational! Users can now:

- Submit sign language queries through the sign recognition interface
- Track their support tickets in the dashboard
- View bank responses directly in their account
- Mark tickets as resolved when satisfied

The bank support team will receive queries via email and can respond directly, with responses automatically appearing in the user's dashboard.

---

**Last Updated**: December 2024
**Version**: 1.0.0
