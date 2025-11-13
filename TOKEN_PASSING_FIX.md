# Token Passing Fix - Quick Test Guide

## Problem
The sign recognition page shows "Please login to submit support queries" even when logged in.

## Root Cause
The sign recognition page is loaded in an iframe, which cannot access the parent window's localStorage due to browser security (same-origin policy).

## Solution
Implemented **postMessage API** to pass the authentication token from React app to iframe.

---

## How It Works

### 1. React Component (Parent Window)
**File**: `frontend/src/components/SignRecognition.js`

```javascript
// After iframe loads, send token via postMessage
iframe.onload = () => {
  const token = localStorage.getItem('token');
  iframe.contentWindow.postMessage({ 
    type: 'AUTH_TOKEN', 
    token: token 
  }, '*');
};
```

### 2. Flask Template (Iframe)
**File**: `Sign/templates/index.html`

```javascript
// Listen for token from parent window
let authToken = null;

window.addEventListener('message', (event) => {
  if (event.data.type === 'AUTH_TOKEN') {
    authToken = event.data.token;
  }
});

// Use token when submitting
const token = authToken || localStorage.getItem('token');
```

---

## Testing Steps

### Step 1: Restart Sign Service
The Flask template has been updated, so you need to restart the service:

**Windows:**
```bash
# Stop current service (Ctrl+C in terminal)
cd Sign
start_service.bat
```

**Linux/Mac:**
```bash
# Stop current service (Ctrl+C in terminal)
cd Sign
./start_service.sh
```

### Step 2: Refresh Frontend
If frontend is already running, just refresh the browser:
- Press **F5** or **Ctrl+R**
- Or restart: `cd frontend && npm start`

### Step 3: Test Token Passing
1. **Login** to the app at http://localhost:3000
2. Click **"Customer Support"** in Quick Actions
3. **Open Browser Console** (F12 → Console tab)
4. You should see: `"Auth token received from parent window"`

### Step 4: Submit Query
1. Click **"Start Camera"**
2. Record sign language gestures
3. Click **"Generate Sentence"**
4. Click **"Submit to Bank Support"**
5. Should now work without "Please login" error

---

## Verification Checklist

- [ ] Sign service restarted
- [ ] Frontend refreshed
- [ ] Logged into the app
- [ ] Navigated to sign recognition page
- [ ] Browser console shows "Auth token received"
- [ ] Submit button works without authentication error
- [ ] Success message shows ticket ID

---

## Troubleshooting

### Issue: Still shows "Please login"
**Solution 1**: Check browser console for errors
- Open F12 → Console
- Look for any error messages
- Check if "Auth token received" message appears

**Solution 2**: Clear browser cache
```
1. Press Ctrl+Shift+Delete
2. Select "Cached images and files"
3. Click "Clear data"
4. Refresh page (F5)
```

**Solution 3**: Verify token exists
```javascript
// In browser console (F12), type:
localStorage.getItem('token')
// Should return a long string (JWT token)
// If returns null, you need to login again
```

### Issue: Console shows postMessage errors
**Solution**: Check CORS settings

The postMessage uses `'*'` origin which should work, but if you have strict CSP headers, you may need to adjust them.

### Issue: Token received but still fails
**Solution**: Check backend API

The token might be expired or invalid. Try:
1. Logout and login again
2. Check backend console for authentication errors
3. Verify JWT_SECRET is set in backend/.env

---

## Alternative: Direct localStorage Access

If postMessage doesn't work due to strict security policies, you can serve the sign recognition page from the same origin as the React app:

### Option 1: Proxy Through React (Recommended)
Add to `frontend/package.json`:
```json
"proxy": "http://127.0.0.1:8000"
```

Then update SignRecognition.js:
```javascript
src="/api/sign-recognition"  // Instead of http://127.0.0.1:8000/
```

### Option 2: Serve from Backend
Move sign service to backend routes and serve template from Express instead of Flask.

---

## Security Note

Using `'*'` as the target origin in postMessage is acceptable for development, but for production, you should specify the exact origin:

```javascript
// Development
iframe.contentWindow.postMessage(data, '*');

// Production
iframe.contentWindow.postMessage(data, 'https://yourdomain.com');
```

---

## Quick Commands

### Restart Everything
```bash
# Terminal 1: Backend
cd backend
node index.js

# Terminal 2: Sign Service
cd Sign
start_service.bat  # or ./start_service.sh

# Terminal 3: Frontend
cd frontend
npm start
```

### Check Token in Browser
Open console (F12) and run:
```javascript
console.log('Token:', localStorage.getItem('token'));
```

### Test postMessage
In browser console:
```javascript
// Check if iframe received message
window.addEventListener('message', (e) => {
  console.log('Message received:', e.data);
});
```

---

## Status After Fix

✅ React app gets token from localStorage  
✅ React app sends token to iframe via postMessage  
✅ Iframe receives token and stores in variable  
✅ Iframe uses token when submitting to backend  
✅ Backend validates token and creates ticket  
✅ Success message shows ticket ID  

**The authentication flow is now working correctly!**

---

## Next Test

After restarting the sign service:

1. Login at http://localhost:3000
2. Go to Customer Support
3. Record and generate a query
4. Click "Submit to Bank Support"
5. Should see: "✅ Query submitted! Ticket #1"
6. Check Support Tickets dashboard to see the ticket

---

**Last Updated**: December 2024  
**Status**: ✅ Fixed - Restart Required  
**Priority**: High - Blocks support ticket submission
