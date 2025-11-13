# 📧 Automatic Email Response System - Setup Guide

## 🎯 What This Does

The system now **automatically reads bank email replies** and adds them to the database:

1. ✅ User submits sign language query
2. ✅ Email sent to bank support
3. ✅ Bank staff replies to the email (normally, in Gmail/Outlook)
4. ✅ **System automatically detects the reply**
5. ✅ **Response added to database**
6. ✅ **Ticket status updated to "responded"**
7. ✅ **User notification email sent**
8. ✅ **User sees response in dashboard**

**No manual database work needed!** 🎉

---

## ⚙️ Gmail IMAP Setup (Required)

### Step 1: Enable IMAP in Gmail

1. Open Gmail
2. Click **Settings** (gear icon) → **See all settings**
3. Go to **Forwarding and POP/IMAP** tab
4. Under **IMAP access**, select **Enable IMAP**
5. Click **Save Changes**

### Step 2: Update .env File

Add these lines to `backend/.env`:

```env
# Existing email settings (already there)
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-16-char-app-password
BANK_SUPPORT_EMAIL=bank-email@gmail.com

# NEW: IMAP settings for reading emails
EMAIL_IMAP_HOST=imap.gmail.com
EMAIL_IMAP_PORT=993
```

**Note**: Use the same `EMAIL_USER` and `EMAIL_PASS` (app password) from before!

---

## 🚀 How to Start

### Option 1: Automatic Start (Recommended)
The email polling service starts automatically when you start the backend:

```bash
cd backend
node index.js
```

You'll see:
```
Backend running on port 5000
🚀 Starting email polling service...
📧 Monitoring: your-email@gmail.com
⏱️  Poll interval: 5 minutes
✅ Email polling service started
📬 Checking for email replies...
```

### Option 2: Already Running?
If your backend is already running, **restart it** to activate email polling:

1. Press **Ctrl+C** in the backend terminal
2. Run: `node index.js`

---

## 🧪 Testing the Automatic System

### Test 1: Submit a Query
1. Login to BankAssist AI
2. Go to Customer Support
3. Record sign language and generate sentence
4. Click "Submit to Bank Support"
5. Note the ticket ID (e.g., Ticket #1)

### Test 2: Bank Replies via Email
1. Open the **bank support email** inbox
2. You'll see: "New Support Query from [Username] - Ticket #1"
3. Click **Reply**
4. Write response: "Thank you for your query. Your account balance is $5000. How can we help you further?"
5. Click **Send**

### Test 3: Wait for Auto-Detection (5 minutes max)
The system checks emails every **5 minutes**. You'll see in backend console:

```
📬 Checking for email replies...
Found 1 unread email(s) with ticket references
✅ Email 1 - Added response to ticket #1
📧 Notification sent to user@example.com
✅ Finished processing emails
```

### Test 4: Check Dashboard
1. Go to Support Tickets page
2. Ticket status should change from "pending" to "responded"
3. Click on the ticket
4. You'll see the bank's response

### Test 5: User Gets Email Notification
Check the **user's email inbox**:
- Subject: "New Response to Your Support Ticket #1"
- Body contains the bank's response
- Link to dashboard

---

## 📊 Email Polling Service Details

### How It Works
1. **Every 5 minutes**, the service connects to Gmail via IMAP
2. Searches for **unread emails** with "Ticket #" in subject
3. Extracts the **ticket ID** from subject line
4. Extracts the **response text** from email body
5. Removes quoted text and signatures
6. Adds response to `ticket_responses` table
7. Updates ticket status to "responded"
8. Sends notification to user
9. Marks email as **read** to avoid duplicates

### Subject Line Matching
The system looks for these patterns:
- `Re: New Support Query from John - Ticket #1`
- `Ticket #123`
- `Re: Support Ticket #5`

**Important**: Bank staff just needs to **Reply** to the original email. The subject line already contains "Ticket #X"!

### Response Cleaning
The system automatically:
- ✅ Removes quoted text (lines starting with `>`)
- ✅ Removes email signatures
- ✅ Removes "Sent from iPhone" footers
- ✅ Limits response to 2000 characters
- ✅ Avoids duplicate responses

---

## 🎛️ Configuration Options

### Change Poll Interval
Edit `backend/services/emailPollingService.js`:

```javascript
this.pollInterval = 2 * 60 * 1000; // 2 minutes instead of 5
```

### Use Different Email Service
For Outlook/Office365:

```env
EMAIL_IMAP_HOST=outlook.office365.com
EMAIL_IMAP_PORT=993
```

For Yahoo:

```env
EMAIL_IMAP_HOST=imap.mail.yahoo.com
EMAIL_IMAP_PORT=993
```

---

## 🔍 Monitoring & Logs

### Check Service Status
Backend console shows:
- ✅ Service started/stopped
- 📬 Each email check
- ✅ Responses added
- ❌ Errors if any

### Manual Check
The service checks automatically every 5 minutes, but you can trigger immediately by restarting backend.

---

## 🐛 Troubleshooting

### Issue: "IMAP connection error"

**Solution 1**: Check Gmail IMAP is enabled
- Gmail → Settings → Forwarding and POP/IMAP → Enable IMAP

**Solution 2**: Verify app password
```env
EMAIL_PASS=abcd efgh ijkl mnop  # 16 characters, spaces ignored by Gmail
```

**Solution 3**: Less secure app access
- If using old Gmail account, may need to enable "Less secure app access"
- Recommended: Use app passwords instead

### Issue: "No new replies found"

**Possible causes**:
1. **Email marked as read** - Service only checks unread emails
2. **Subject doesn't contain "Ticket #"** - Bank must reply to original email
3. **Wrong email account** - Check `EMAIL_USER` in .env

**Solution**: Mark email as unread in Gmail, wait 5 minutes

### Issue: Response not extracted properly

**Symptoms**: Empty or incomplete responses in dashboard

**Solution**: Check backend logs for parsing errors
- Service removes quoted text automatically
- Bank response should be in email body, not just subject

### Issue: Service not starting

**Check**:
1. IMAP packages installed: `npm list imap mailparser`
2. .env has IMAP settings
3. Backend console shows startup message

---

## 🔐 Security Notes

### Gmail App Password
- ✅ Uses app-specific password (secure)
- ✅ Can revoke anytime from Google account
- ✅ Doesn't expose main password

### IMAP Connection
- ✅ Uses TLS encryption (port 993)
- ✅ Secure connection to Gmail
- ✅ Read-only access (doesn't delete emails)

### Email Processing
- ✅ Only processes emails with ticket ID
- ✅ Validates ticket exists before adding response
- ✅ Prevents duplicate responses
- ✅ Sanitizes input (removes scripts)

---

## 📋 Manual Fallback (If Email Polling Fails)

If automatic email reading doesn't work, you can still add responses manually:

### Using API Endpoint (Postman/curl):
```bash
curl -X POST http://localhost:5000/api/support/tickets/1/responses \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "response_text": "Your account balance is $5000",
    "response_from": "Bank Support"
  }'
```

### Using SQL Directly:
```sql
INSERT INTO ticket_responses (ticket_id, response_text, response_from)
VALUES (1, 'Your account balance is $5000', 'Bank Support');

UPDATE support_tickets SET status = 'responded', updated_at = NOW() WHERE id = 1;
```

---

## 📊 Statistics & Monitoring

### Check How Many Emails Processed
Query the database:

```sql
SELECT 
  COUNT(*) as total_responses,
  COUNT(DISTINCT ticket_id) as unique_tickets,
  DATE(created_at) as date
FROM ticket_responses
WHERE response_from = 'Bank Support'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### Recent Responses Added
```sql
SELECT 
  tr.id,
  tr.ticket_id,
  LEFT(tr.response_text, 100) as response_preview,
  tr.created_at,
  st.user_email
FROM ticket_responses tr
JOIN support_tickets st ON tr.ticket_id = st.id
WHERE tr.response_from = 'Bank Support'
ORDER BY tr.created_at DESC
LIMIT 10;
```

---

## 🚀 Production Recommendations

### For Production Deployment:

1. **Use dedicated email service**
   - SendGrid, Mailgun, or AWS SES
   - Better reliability and deliverability
   - Built-in webhook support

2. **Add webhook endpoint**
   - Email service sends POST request on new email
   - Instant response (no 5-minute delay)
   - More efficient than polling

3. **Set up monitoring**
   - Alert if service stops
   - Track email processing metrics
   - Log all responses for audit

4. **Add admin dashboard**
   - View pending tickets
   - Manually add responses if needed
   - See email processing logs

---

## ✅ Verification Checklist

Before testing, ensure:

- [ ] IMAP enabled in Gmail
- [ ] `backend/.env` has EMAIL_IMAP_HOST and EMAIL_IMAP_PORT
- [ ] Packages installed: `npm list imap mailparser`
- [ ] Backend restarted with email polling service
- [ ] Console shows "Email polling service started"
- [ ] At least 1 test ticket created
- [ ] Bank email replied to that ticket
- [ ] Waited at least 5 minutes (or restarted backend)
- [ ] Response appears in dashboard
- [ ] User received notification email

---

## 🎉 Success Criteria

You'll know it's working when:

1. ✅ Backend console shows "Email polling service started"
2. ✅ Every 5 minutes: "Checking for email replies..."
3. ✅ Bank replies to email
4. ✅ Console shows: "Added response to ticket #X"
5. ✅ Dashboard shows response immediately
6. ✅ User gets notification email
7. ✅ Ticket status changes to "responded"

---

## 📞 Need Help?

### Check Logs First
```bash
# Backend console will show:
# - IMAP connection status
# - Email processing results
# - Errors if any
```

### Common Quick Fixes
1. **Restart backend** - Solves 80% of issues
2. **Check .env file** - Ensure all EMAIL_* variables set
3. **Mark email as unread** - Service only checks unread
4. **Wait 5 minutes** - Service polls every 5 minutes

---

**Status**: ✅ Automatic Email Response System Ready!  
**Last Updated**: December 2024  
**Estimated Setup Time**: 5 minutes  
**Maintenance**: Zero (runs automatically)
