# ✅ Support Ticket System Setup Checklist

Use this checklist to track your setup progress. Check off each item as you complete it.

---

## 📋 Pre-Setup Checklist

- [ ] Have at least 1 Gmail account available
- [ ] PostgreSQL database is running
- [ ] Node.js and npm installed
- [ ] Python 3.8+ installed
- [ ] All project dependencies installed

---

## 🔑 Gmail Configuration

### Step 1: Enable 2-Step Verification
- [ ] Go to https://myaccount.google.com/security
- [ ] Click "2-Step Verification"
- [ ] Follow setup process if not already enabled
- [ ] Verify phone number
- [ ] Complete 2-Step Verification setup

### Step 2: Generate App Password
- [ ] Navigate to https://myaccount.google.com/apppasswords
- [ ] Select app: **Mail**
- [ ] Select device: **Other (Custom name)**
- [ ] Enter name: **BankAssist AI**
- [ ] Click **Generate**
- [ ] Copy the 16-character password
- [ ] Save it securely (you'll need it for .env)

**App Password**: `________________` (write it down temporarily)

---

## 🗄️ Database Setup

### Step 1: Connect to Database
- [ ] Open PostgreSQL client (pgAdmin/psql/DBeaver)
- [ ] Connect to your database
- [ ] Verify connection successful

### Step 2: Run Schema File
Choose your method:

**Method A: Using psql command line**
```bash
psql -U your_username -d your_database_name -f backend/database_schema_tickets.sql
```
- [ ] Command executed successfully
- [ ] No errors displayed

**Method B: Using pgAdmin**
- [ ] Open Query Tool
- [ ] Open file: `backend/database_schema_tickets.sql`
- [ ] Execute (F5)
- [ ] Check "Messages" tab for success

**Method C: Copy-paste in any SQL client**
- [ ] Open `backend/database_schema_tickets.sql`
- [ ] Copy entire contents
- [ ] Paste in SQL client query window
- [ ] Execute
- [ ] Check for success message

### Step 3: Verify Tables Created
Run this query:
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('support_tickets', 'ticket_responses');
```

- [ ] Query returns 2 rows
- [ ] `support_tickets` table exists
- [ ] `ticket_responses` table exists

### Step 4: Test Table Structure
Run this query:
```sql
SELECT * FROM support_tickets LIMIT 0;
SELECT * FROM ticket_responses LIMIT 0;
```

- [ ] Both queries run without errors
- [ ] Tables are empty (as expected)

---

## ⚙️ Backend Configuration

### Step 1: Locate .env File
- [ ] Open `backend/.env` file
- [ ] If doesn't exist, create it in `backend/` folder

### Step 2: Add Email Configuration
Add these lines (replace with your values):

```env
# Email Service Configuration
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-16-char-app-password
BANK_SUPPORT_EMAIL=bank-email@gmail.com

# Optional (leave as default)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
```

- [ ] Added `EMAIL_USER` with your Gmail address
- [ ] Added `EMAIL_PASS` with app password (16 chars, no spaces)
- [ ] Added `BANK_SUPPORT_EMAIL` with bank support Gmail
- [ ] Saved file

### Step 3: Verify Other .env Variables
Check these exist (should already be there):

- [ ] `DB_USER` (PostgreSQL username)
- [ ] `DB_HOST` (usually `localhost`)
- [ ] `DB_NAME` (your database name)
- [ ] `DB_PASSWORD` (PostgreSQL password)
- [ ] `DB_PORT` (usually `5432`)
- [ ] `JWT_SECRET` (for authentication)
- [ ] `PORT` (usually `5000`)

### Step 4: Install Backend Dependencies
```bash
cd backend
npm install nodemailer
```

- [ ] Command completed successfully
- [ ] No errors displayed
- [ ] `node_modules` folder exists

---

## 🐍 Sign Service Configuration

### Step 1: Install Python Dependencies
```bash
cd Sign
pip install requests==2.31.0
```

- [ ] Command completed successfully
- [ ] No errors displayed

### Step 2: Verify Other Dependencies
```bash
pip list | grep -E "flask|tensorflow|mediapipe|ctransformers"
```

Should show:
- [ ] Flask 3.0.x
- [ ] tensorflow 2.15.x
- [ ] mediapipe 0.10.x
- [ ] ctransformers (any version)

---

## ⚛️ Frontend Configuration

### Step 1: Install Frontend Dependencies
```bash
cd frontend
npm install axios react-router-dom react-icons
```

- [ ] Command completed successfully
- [ ] No errors displayed

### Step 2: Verify Build
```bash
npm run build
```

- [ ] Build completed successfully
- [ ] `build/` folder created
- [ ] No errors (warnings are OK)

---

## 🚀 Start Services

### Backend Server
```bash
cd backend
node index.js
```

Expected output:
```
Server running on port 5000
Database connected
```

- [ ] Backend running on port 5000
- [ ] No database connection errors
- [ ] Console shows "Server running" message

**Keep this terminal open!**

### Sign Recognition Service
**Windows:**
```bash
cd Sign
start_service.bat
```

**Linux/Mac:**
```bash
cd Sign
chmod +x start_service.sh
./start_service.sh
```

Expected output:
```
Loading sign language model...
Starting Flask server on http://127.0.0.1:8000
```

- [ ] Sign service running on port 8000
- [ ] Model loaded successfully
- [ ] No import errors

**Keep this terminal open!**

### Frontend
```bash
cd frontend
npm start
```

Expected output:
```
Compiled successfully!
Local: http://localhost:3000
```

- [ ] Frontend running on port 3000
- [ ] Browser opens automatically
- [ ] No compilation errors

**Keep this terminal open!**

---

## 🧪 Testing Phase

### Test 1: Basic Login
- [ ] Navigate to http://localhost:3000
- [ ] Click "Login"
- [ ] Enter credentials
- [ ] Login successful
- [ ] Dashboard loads

### Test 2: Navigate to Sign Recognition
- [ ] Click "Customer Support" in Quick Actions
- [ ] Sign recognition page loads
- [ ] Camera permission requested
- [ ] Allow camera access
- [ ] Video feed visible

### Test 3: Record & Generate Query
- [ ] Click "Start Recording"
- [ ] Perform sign language gestures (at least 5 seconds)
- [ ] Click "Stop Recording"
- [ ] Recording indicator shows
- [ ] Click "Generate Sentence"
- [ ] Wait for processing
- [ ] Generated sentence appears

**Generated Sentence**: ________________________________

### Test 4: Submit to Bank Support
- [ ] Click "Submit to Bank Support" button
- [ ] Wait for response
- [ ] Success message appears
- [ ] Ticket ID displayed (e.g., "Ticket #1 created")

**Ticket ID**: ________

### Test 5: Check Bank Email
- [ ] Open bank support email inbox
- [ ] New email received
- [ ] Subject: "New Support Query from [Username] - Ticket #[ID]"
- [ ] Email contains query text
- [ ] Email shows user's email address

### Test 6: Check User Confirmation Email
- [ ] Open user email inbox
- [ ] Confirmation email received
- [ ] Subject: "Your Support Ticket Has Been Submitted"
- [ ] Email contains ticket ID
- [ ] Email contains query text

### Test 7: View in Dashboard
- [ ] Navigate to Dashboard (http://localhost:3000/dashboard)
- [ ] Click "Support Tickets" in Quick Actions
- [ ] Support Tickets page loads
- [ ] Ticket appears in list
- [ ] Status shows "pending"
- [ ] Click on ticket
- [ ] Details panel opens
- [ ] Query text displayed
- [ ] "Sign Language" badge visible

### Test 8: Bank Reply
- [ ] In bank email, click "Reply" on support query
- [ ] Write a test response (e.g., "Thank you for your query. We're processing your request.")
- [ ] Send reply to user's email address
- [ ] Email sent successfully

**Response Text**: ________________________________

### Test 9: Add Response to System (Manual)
Since webhook isn't implemented, manually add response:

**Using API (Postman/curl):**
```bash
curl -X POST http://localhost:5000/api/support/tickets/1/responses \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"response_text": "Your response text here", "response_from": "bank"}'
```

**Or using SQL:**
```sql
INSERT INTO ticket_responses (ticket_id, response_text, response_from, created_at)
VALUES (1, 'Your response text here', 'bank', NOW());

UPDATE support_tickets 
SET status = 'responded', updated_at = NOW() 
WHERE id = 1;
```

- [ ] Response added successfully
- [ ] Status updated to "responded"

### Test 10: View Bank Response in Dashboard
- [ ] Refresh Support Tickets page
- [ ] Ticket status changed to "responded"
- [ ] Response count badge appears
- [ ] Click on ticket
- [ ] Bank response visible in details panel
- [ ] Response timestamp shown

### Test 11: Check User Notification Email
- [ ] Open user email inbox
- [ ] Response notification received
- [ ] Subject: "New Response to Your Support Ticket"
- [ ] Email contains response preview
- [ ] Link to dashboard included

### Test 12: Resolve Ticket
- [ ] In ticket details panel
- [ ] Click "Mark as Resolved" button
- [ ] Confirmation appears
- [ ] Status changes to "resolved"
- [ ] Button disappears (or changes)

### Test 13: Filter Tickets
- [ ] Click "All" tab - shows all tickets
- [ ] Click "Pending" tab - shows only pending
- [ ] Click "Responded" tab - shows only responded
- [ ] Click "Resolved" tab - shows only resolved
- [ ] Stats cards update correctly

### Test 14: Stats Verification
Check stats cards show correct numbers:
- [ ] Total Tickets: matches database count
- [ ] Pending: matches pending count
- [ ] Responded: matches responded count
- [ ] Resolved: matches resolved count

---

## ✅ Final Verification

### System Health Check
- [ ] Backend server still running (check terminal)
- [ ] Sign service still running (check terminal)
- [ ] Frontend still running (check terminal)
- [ ] No errors in any terminal

### Database Check
Run this query:
```sql
SELECT 
  COUNT(*) as total_tickets,
  COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
  COUNT(CASE WHEN status = 'responded' THEN 1 END) as responded,
  COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved
FROM support_tickets;
```

- [ ] Query returns data
- [ ] Numbers match dashboard stats
- [ ] At least 1 ticket exists

### API Endpoint Check
Test these URLs (replace TOKEN with your JWT):

1. **Get Tickets**
   ```bash
   curl -H "Authorization: Bearer TOKEN" http://localhost:5000/api/support/tickets
   ```
   - [ ] Returns array of tickets
   - [ ] No errors

2. **Get Ticket Details**
   ```bash
   curl -H "Authorization: Bearer TOKEN" http://localhost:5000/api/support/tickets/1
   ```
   - [ ] Returns ticket with responses
   - [ ] No errors

3. **Get Stats**
   ```bash
   curl -H "Authorization: Bearer TOKEN" http://localhost:5000/api/support/stats
   ```
   - [ ] Returns stats object
   - [ ] No errors

---

## 🎉 Success Criteria

All must be ✅ to consider setup complete:

- [ ] Database tables created and accessible
- [ ] Backend .env configured with email settings
- [ ] All services running without errors
- [ ] Sign language query submitted successfully
- [ ] Bank email received with query
- [ ] User confirmation email received
- [ ] Ticket visible in dashboard
- [ ] Bank response added and visible
- [ ] Response notification email received
- [ ] Ticket marked as resolved successfully
- [ ] All filter tabs working
- [ ] Stats cards showing correct numbers

---

## 📊 Setup Summary

### Time Taken
- Database setup: ________ minutes
- Email configuration: ________ minutes
- Dependencies installation: ________ minutes
- Services startup: ________ minutes
- Testing: ________ minutes
- **Total**: ________ minutes

### Issues Encountered
List any problems you faced:

1. ____________________________________________
2. ____________________________________________
3. ____________________________________________

### Solutions Applied
What fixed the issues:

1. ____________________________________________
2. ____________________________________________
3. ____________________________________________

---

## 📝 Configuration Summary

### Email Accounts Used
- **Sender (EMAIL_USER)**: ____________________
- **Bank Support**: ____________________
- **Test User**: ____________________

### Database Details
- **Host**: ____________________
- **Port**: ____________________
- **Database Name**: ____________________
- **Username**: ____________________

### Service Ports
- Backend: ✅ 5000
- Sign Service: ✅ 8000
- Frontend: ✅ 3000

---

## 🚀 Next Steps

Now that setup is complete:

### Immediate
- [ ] Create a backup of database
- [ ] Document any custom configurations
- [ ] Test with multiple user accounts
- [ ] Test on different browsers

### Short Term (This Week)
- [ ] Set up email webhook for auto-parsing replies
- [ ] Create bank admin interface
- [ ] Add more test data
- [ ] Configure production email service

### Long Term (This Month)
- [ ] Implement real-time notifications
- [ ] Add file attachment support
- [ ] Create mobile app interface
- [ ] Set up monitoring and analytics

---

## 📞 Support

If you encounter issues during setup:

1. **Check Logs**
   - Backend terminal output
   - Sign service terminal output
   - Browser console (F12)

2. **Verify Configuration**
   - `.env` file has all required variables
   - Database tables exist
   - All services running on correct ports

3. **Review Documentation**
   - `SUPPORT_TICKET_SETUP.md` - Detailed setup guide
   - `SUPPORT_TICKET_FILES.md` - File reference
   - `SUPPORT_TICKET_README.md` - Quick overview

4. **Common Issues**
   - Gmail app password: Generate new one
   - Database connection: Check credentials
   - Port conflicts: Change ports in config
   - Module not found: Run `npm install` or `pip install`

---

## ✅ Completion Certificate

I, ________________________, have successfully completed the setup of the BankAssist AI Support Ticket System on _____________ (date).

**System Status**: ✅ Fully Operational

**Components Verified**:
- ✅ Database schema
- ✅ Email integration
- ✅ Backend API
- ✅ Sign recognition service
- ✅ Frontend dashboard
- ✅ End-to-end testing

**Ready for**: ☐ Development  ☐ Testing  ☐ Production

---

**Last Updated**: December 2024
**Checklist Version**: 1.0.0
