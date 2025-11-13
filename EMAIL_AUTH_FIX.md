# 🔧 Email Authentication Fix Guide

## ❌ Current Error
```
Error: Not authenticated
```

## 🎯 Root Cause
The system needs to check the **BANK support email** (`abhiadar99@gmail.com`) inbox for replies, but it doesn't have the app password for that account.

---

## ✅ Solution: Generate App Password for Bank Email

### Step 1: Login to Bank Gmail Account
- Go to https://mail.google.com
- Login with: **abhiadar99@gmail.com**

### Step 2: Enable 2-Step Verification (if not already)
1. Go to https://myaccount.google.com/security
2. Click **2-Step Verification**
3. Follow setup if not enabled
4. Verify phone number

### Step 3: Generate App Password
1. Go to https://myaccount.google.com/apppasswords
2. Or: Google Account → Security → App passwords
3. Select app: **Mail**
4. Select device: **Other (Custom name)**
5. Enter name: **BankAssist AI Backend**
6. Click **Generate**
7. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

### Step 4: Enable IMAP in Gmail
1. Open Gmail for **abhiadar99@gmail.com**
2. Click Settings (gear icon) → **See all settings**
3. Go to **Forwarding and POP/IMAP** tab
4. Under IMAP access, select **Enable IMAP**
5. Click **Save Changes**

### Step 5: Update .env File
Edit `backend/.env` and replace this line:

```env
BANK_EMAIL_PASS=YOUR_BANK_EMAIL_APP_PASSWORD_HERE
```

With:

```env
BANK_EMAIL_PASS=abcdefghijklmnop
```
*(Replace with your actual 16-character app password, no spaces)*

### Step 6: Restart Backend
Stop the current backend (Ctrl+C) and restart:

```bash
cd backend
node index.js
```

You should see:
```
Backend running on port 5000
🚀 Starting email polling service...
📧 Monitoring BANK email: abhiadar99@gmail.com
⏱️  Poll interval: 1 minutes
✅ Email polling service started
📬 Checking for email replies...
```

---

## 🔄 How It Now Works (Corrected)

### Before (Wrong):
❌ System was checking **user's email** (adarsh.ds22@sahyadri.edu.in)  
❌ Reading user's own replies instead of bank's replies

### After (Correct):
✅ System checks **BANK email** (abhiadar99@gmail.com)  
✅ When bank staff replies to a query, system reads from bank's **Sent** folder  
✅ Only bank replies are added to dashboard  

---

## 📧 Email Flow (Fixed)

1. **User submits query** via sign language
   - Email sent FROM: `adarsh.ds22@sahyadri.edu.in`
   - Email sent TO: `abhiadar99@gmail.com` (bank)
   - Subject: "New Support Query from John - Ticket #1"

2. **Bank staff opens Gmail** (`abhiadar99@gmail.com`)
   - Sees the query email
   - Clicks **Reply**
   - Types response: "Your account balance is $5000"
   - Clicks **Send**

3. **Email polling service** (checks bank inbox)
   - Connects to `abhiadar99@gmail.com` via IMAP
   - Searches for emails with "Ticket #" in subject
   - Finds the reply
   - Extracts response text
   - Adds to database
   - Updates ticket status to "responded"

4. **User notification**
   - System sends email to user
   - User gets notified of response
   - User sees response in dashboard

---

## 🧪 Testing Steps

### 1. Submit Test Query
- Login to BankAssist AI
- Go to Customer Support
- Record sign language
- Generate sentence
- Click "Submit to Bank Support"
- Note ticket ID (e.g., #1)

### 2. Bank Receives Email
- Check inbox of `abhiadar99@gmail.com`
- Should see: "New Support Query from [User] - Ticket #1"
- Email contains the user's query

### 3. Bank Replies
- In Gmail (`abhiadar99@gmail.com`), click **Reply** on that email
- Write response: "Thank you for contacting us. Your account balance is $5000. How can we help further?"
- Click **Send**

### 4. Wait for Auto-Detection
- System checks every **1 minute** (currently set)
- Watch backend console for:
```
📬 Checking for email replies...
Found 1 unread email(s) with ticket references
✅ Email 1 - Added response to ticket #1
📧 Notification sent to user@example.com
✅ Finished processing emails
```

### 5. Verify in Dashboard
- Go to Support Tickets page
- Ticket #1 status should be "responded"
- Click on ticket
- Should see bank's response text

---

## 🔍 Troubleshooting

### Error: "Not authenticated"
**Cause**: No app password for bank email  
**Fix**: Generate app password as shown above

### Error: "IMAP connection error"
**Cause**: IMAP not enabled in Gmail  
**Fix**: Enable IMAP in Gmail settings

### No emails detected
**Causes**:
1. Email marked as read - mark as unread
2. Subject doesn't contain "Ticket #" - ensure replying to original email
3. Wrong poll interval - currently set to 1 minute

**Check**: Backend console shows:
```
📬 Checking for email replies...
Found 0 unread email(s) with ticket references
```

### Response not added to database
**Cause**: Response text too short or duplicate  
**Check**: Backend logs show why email was skipped

---

## ⚙️ Configuration

### Current Settings (in .env):
```env
# Sends emails (query to bank, confirmations, notifications)
EMAIL_USER=adarsh.ds22@sahyadri.edu.in
EMAIL_PASS=gujtzvpdgaqiboaq

# Receives replies from bank staff
BANK_SUPPORT_EMAIL=abhiadar99@gmail.com
BANK_EMAIL_PASS=<NEED TO ADD>

# IMAP for reading bank inbox
EMAIL_IMAP_HOST=imap.gmail.com
EMAIL_IMAP_PORT=993
```

### Poll Interval
Currently: **1 minute** (very frequent for testing)

To change to 5 minutes, edit `backend/services/emailPollingService.js`:
```javascript
this.pollInterval = 5 * 60 * 1000; // 5 minutes
```

---

## ✅ Checklist

Before testing, ensure:

- [ ] Logged into bank Gmail (`abhiadar99@gmail.com`)
- [ ] 2-Step Verification enabled for bank account
- [ ] App password generated for bank account
- [ ] IMAP enabled in bank Gmail settings
- [ ] `BANK_EMAIL_PASS` added to `.env` file
- [ ] Backend restarted with new config
- [ ] Console shows "Monitoring BANK email: abhiadar99@gmail.com"
- [ ] No "Not authenticated" error in console

---

## 📊 Expected Behavior

### Backend Console (Success):
```
Backend running on port 5000
🚀 Starting email polling service...
📧 Monitoring BANK email: abhiadar99@gmail.com
⏱️  Poll interval: 1 minutes
✅ Email polling service started
📬 Checking for email replies...
Found 1 unread email(s) with ticket references
✅ Email 1 - Added response to ticket #1
📧 Notification sent to user@example.com
✅ Finished processing emails
```

### Dashboard:
- Ticket shows status "responded" (green badge)
- Response visible in ticket details
- User receives email notification

---

## 🎯 Quick Fix Summary

1. Generate app password for `abhiadar99@gmail.com`
2. Enable IMAP in Gmail for that account
3. Update `.env`: `BANK_EMAIL_PASS=your-16-char-password`
4. Restart backend
5. Test: Submit query → Bank replies → Wait 1 min → Check dashboard

**That's it!** The system will now correctly read bank replies and display them in the dashboard.

---

**Status**: ⚠️ Needs bank email app password  
**Priority**: High - Blocks automatic response feature  
**Estimated Fix Time**: 5 minutes
