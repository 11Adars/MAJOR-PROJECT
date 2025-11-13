# Support Ticket System - File Reference

## 📁 Files Added/Modified

### Backend Files

#### New Files Created

1. **`backend/controllers/supportController.js`**
   - Purpose: Business logic for support ticket operations
   - Functions:
     - `submitTicket()` - Create new ticket and send emails
     - `getUserTickets()` - Get all tickets for logged-in user (with filters)
     - `getTicketDetails()` - Get single ticket with all responses
     - `addTicketResponse()` - Add bank response to ticket
     - `resolveTicket()` - Mark ticket as resolved
     - `getTicketStats()` - Get ticket statistics for user

2. **`backend/database_schema_tickets.sql`**
   - Purpose: Database schema for support tickets
   - Tables:
     - `support_tickets` - Main ticket table with user_id, query, status
     - `ticket_responses` - Responses from bank to tickets
   - Indexes: Performance optimization for queries

#### Modified Files

3. **`backend/utils/emailService.js`**
   - Added Functions:
     - `sendQueryToBank()` - Send query to bank support email
     - `sendQueryConfirmation()` - Confirm submission to user
     - `notifyUserOfResponse()` - Notify user when bank replies
   - Uses HTML email templates with branded styling

4. **`backend/index.js`**
   - Added Routes:
     ```javascript
     POST   /api/support/tickets              // Submit new ticket
     GET    /api/support/tickets              // Get user's tickets (with filters)
     GET    /api/support/tickets/:ticketId    // Get ticket details
     POST   /api/support/tickets/:ticketId/responses  // Add response
     PATCH  /api/support/tickets/:ticketId/resolve    // Mark resolved
     GET    /api/support/stats                // Get ticket stats
     ```

---

### Sign Recognition Service Files

#### Modified Files

5. **`Sign/sign_service.py`**
   - Added Endpoint:
     - `/api/submit-to-support` - Forward query to backend with auth
   - Features:
     - Receives generated sentence and auth token from frontend
     - Forwards to backend API with proper headers
     - Returns ticket ID on success

6. **`Sign/templates/index.html`**
   - Added UI Elements:
     - "Submit to Bank Support" button
     - Success message display
     - Error handling
   - JavaScript:
     - `submitToSupportBtn` event listener
     - Fetches auth token from localStorage
     - Displays ticket ID on success

7. **`Sign/requirements.txt`**
   - Added: `requests==2.31.0` for HTTP requests to backend

---

### Frontend Files

#### New Files Created

8. **`frontend/src/components/SupportTickets.js`**
   - Purpose: Dashboard component for viewing/managing tickets
   - Features:
     - Stats cards (total, pending, responded, resolved)
     - Filter tabs (all, pending, responded, resolved)
     - Ticket list with click-to-view
     - Detailed ticket view with responses
     - Mark as resolved functionality
     - Loading and empty states
   - API Calls:
     - GET `/api/support/tickets` - Fetch tickets
     - GET `/api/support/tickets/:id` - Fetch details
     - PATCH `/api/support/tickets/:id/resolve` - Resolve
     - GET `/api/support/stats` - Fetch stats

9. **`frontend/src/components/SupportTickets.css`**
   - Purpose: Complete styling for Support Tickets component
   - Styling:
     - Purple theme matching BankAssist AI (#667eea)
     - Responsive grid layouts
     - Status badges with color coding
     - Hover effects and animations
     - Mobile-responsive design
     - Loading spinners and empty states

#### Modified Files

10. **`frontend/src/App.js`**
    - Added Import:
      ```javascript
      import SupportTickets from './components/SupportTickets';
      ```
    - Added Route:
      ```javascript
      <Route path="/support-tickets" 
             element={isAuthenticated ? <SupportTickets /> : <Navigate to="/login" />} />
      ```

11. **`frontend/src/components/QuickActions.js`**
    - Added Button:
      ```javascript
      <button className="action-btn" onClick={() => navigate('/support-tickets')}>
        <FaTicketAlt /> Support Tickets
      </button>
      ```

---

## 🗂️ File Organization

```
MAJOR-PROJECT/
│
├── backend/
│   ├── controllers/
│   │   └── supportController.js          [NEW] - Ticket business logic
│   ├── utils/
│   │   └── emailService.js               [MODIFIED] - Added 3 email functions
│   ├── database_schema_tickets.sql       [NEW] - Database schema
│   └── index.js                          [MODIFIED] - Added 6 routes
│
├── Sign/
│   ├── templates/
│   │   └── index.html                    [MODIFIED] - Added submit button
│   ├── sign_service.py                   [MODIFIED] - Added submit endpoint
│   └── requirements.txt                  [MODIFIED] - Added requests
│
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── SupportTickets.js         [NEW] - Ticket dashboard component
│       │   ├── SupportTickets.css        [NEW] - Component styling
│       │   └── QuickActions.js           [MODIFIED] - Added tickets link
│       └── App.js                        [MODIFIED] - Added route
│
├── SUPPORT_TICKET_SETUP.md               [NEW] - Setup guide
└── SUPPORT_TICKET_FILES.md               [NEW] - This file
```

---

## 🔄 Data Flow

### Submit Ticket Flow

```
1. User records sign language
   ↓
2. Sign/templates/index.html
   - Click "Submit to Bank Support"
   ↓
3. Sign/sign_service.py
   - POST /api/submit-to-support
   - Receives: { query_text, auth_token }
   ↓
4. backend/controllers/supportController.js
   - submitTicket()
   - Creates ticket in database
   ↓
5. backend/utils/emailService.js
   - sendQueryToBank() - Email to bank
   - sendQueryConfirmation() - Email to user
   ↓
6. Returns ticket ID to frontend
```

### View Tickets Flow

```
1. User navigates to /support-tickets
   ↓
2. frontend/src/components/SupportTickets.js
   - useEffect() runs on mount
   ↓
3. GET /api/support/tickets
   - backend/controllers/supportController.js
   - getUserTickets()
   ↓
4. Returns filtered tickets
   ↓
5. Display in ticket list with stats
```

### Bank Response Flow

```
1. Bank receives email query
   ↓
2. Bank replies to user's email
   ↓
3. [Manual/Webhook] Add response to database
   - POST /api/support/tickets/:ticketId/responses
   ↓
4. backend/controllers/supportController.js
   - addTicketResponse()
   - Updates status to 'responded'
   ↓
5. backend/utils/emailService.js
   - notifyUserOfResponse()
   - Sends notification email
   ↓
6. User views response in dashboard
```

---

## 🔑 Key Code Sections

### Authentication Flow

All API calls require JWT token:

```javascript
// Frontend - SupportTickets.js
const token = localStorage.getItem('token');
const config = {
  headers: { Authorization: `Bearer ${token}` }
};
```

### Email Templates

Located in `backend/utils/emailService.js`:

- **Bank Query Email**: Professional HTML with query details
- **User Confirmation**: Receipt acknowledgment with ticket ID
- **Response Notification**: Alert when bank replies

### Database Queries

Located in `backend/controllers/supportController.js`:

- Uses parameterized queries for security
- Includes JOIN operations for ticket + responses
- Implements filtering by status
- Uses transactions for data consistency

### Status Management

Ticket status transitions:

```
pending → responded → resolved
   ↑          ↓
   └──────────┘ (can reopen)
```

---

## 📊 Database Schema

### support_tickets

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| user_id | INTEGER | Foreign key to users |
| query_text | TEXT | User's query |
| query_source | VARCHAR(50) | 'sign_language', 'manual', etc. |
| status | VARCHAR(20) | 'pending', 'responded', 'resolved' |
| created_at | TIMESTAMP | When ticket was created |
| updated_at | TIMESTAMP | Last update time |

### ticket_responses

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| ticket_id | INTEGER | Foreign key to support_tickets |
| response_text | TEXT | Bank's response |
| response_from | VARCHAR(100) | 'bank' or 'system' |
| created_at | TIMESTAMP | When response was added |

---

## 🎨 UI Components

### SupportTickets Component Structure

```
SupportTicketsContainer
├── Header
│   ├── Title + Back Button
│   └── New Ticket Button (future)
├── Stats Grid
│   ├── Total Tickets Card
│   ├── Pending Card
│   ├── Responded Card
│   └── Resolved Card
├── Filter Tabs
│   ├── All
│   ├── Pending
│   ├── Responded
│   └── Resolved
└── Main Content (2-column)
    ├── Tickets List
    │   └── Ticket Items (clickable)
    └── Ticket Details Panel
        ├── Query Section
        ├── Metadata
        ├── Responses List
        └── Actions (Mark Resolved)
```

---

## 🔧 Configuration Requirements

### Backend `.env`

```env
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password
BANK_SUPPORT_EMAIL=bank-support@gmail.com
```

### Database Connection

Already configured in `backend/db.js`:
- Uses PostgreSQL
- Connection pooling enabled
- Error handling implemented

---

## ✅ Testing Checklist

### Backend Testing

- [ ] POST /api/support/tickets returns ticket ID
- [ ] GET /api/support/tickets returns user's tickets
- [ ] Filter by status works (pending, responded, resolved)
- [ ] GET /api/support/tickets/:id returns ticket details
- [ ] POST responses updates status correctly
- [ ] PATCH resolve marks ticket as resolved
- [ ] Emails sent successfully

### Frontend Testing

- [ ] /support-tickets route accessible when logged in
- [ ] Stats cards display correct counts
- [ ] Filter tabs show correct tickets
- [ ] Click ticket shows details panel
- [ ] Responses display correctly
- [ ] Mark resolved button works
- [ ] Loading states appear
- [ ] Empty states display correctly

### Integration Testing

- [ ] Sign service submits to backend successfully
- [ ] Ticket appears in dashboard immediately
- [ ] Bank email received with correct content
- [ ] Email has reply-to set to user email
- [ ] User email confirmation received
- [ ] Response notification sent when bank replies

---

## 📝 Notes

### Future Enhancements

1. **Real-time Updates**: WebSocket connection for live updates
2. **Rich Text Editor**: Allow formatting in responses
3. **File Attachments**: Upload images/documents
4. **Search Functionality**: Search through tickets
5. **Export to PDF**: Download ticket history
6. **Admin Portal**: Separate interface for bank staff
7. **Email Webhook**: Auto-parse bank email replies
8. **Push Notifications**: Browser notifications for responses

### Security Considerations

- JWT authentication on all endpoints
- SQL injection prevention (parameterized queries)
- XSS prevention (React auto-escapes)
- CSRF protection (can add tokens)
- Rate limiting (can add middleware)
- Email validation (already implemented)

---

**Last Updated**: December 2024
**Status**: Complete and Ready for Testing
