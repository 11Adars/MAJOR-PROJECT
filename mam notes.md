## Authentication Flow

User Registration → Biometric Enrollment → JWT Token Generation → Protected Routes Access

----------------------------------------------------

## User Authentication System

```1. Face Recognition```

Technology Used: Python Flask + InsightFace (ArcFace Model)

How it Works:

User uploads face image during registration
Python service extracts face embedding using ArcFace model
Embedding stored in database
During login, new image is compared with stored embedding
Threshold-based matching determines authentication success

```2.  Voice Recognition ```

Technology Used: Python Flask + SpeechBrain (ECAPA-TDNN Model)

How it Works:
User records voice sample during registration
Python service extracts speaker embedding and biometric features
Features stored in database
During login, voice comparison using cosine similarity
Multiple feature analysis for robust verification


```3. OTP Verification```
Technology Used: Node.js + Nodemailer

How it Works:

User requests OTP via email
6-digit random OTP generated and sent
OTP stored temporarily with expiry
User enters OTP for verification
JWT token issued upon successful verification


# Adaptive Fusion Approach

Concept: Instead of traditional fusion (requiring all modalities), we implement user-centric adaptive fusion:

Users can choose their preferred authentication method
System supports multiple independent modalities
Maximizes accessibility for deaf and dumb users



## Banking Features Implementation

```Wallet Management```

How it Works:

Each user has a virtual wallet stored in database
Initial balance set to 0 upon registration
Balance updates through add money and transfer operations
Real-time balance display in dashboard

``` Add Money Feature (Razorpay Integration)```

Technology Used: Razorpay Checkout + Order API

Workflow:

User clicks "Add Money" and enters amount
Backend creates Razorpay order using Order API
Frontend opens Razorpay Checkout popup
User completes payment in test mode
Payment success triggers backend verification
User's wallet balance updated in database
Transaction recorded in history

```Peer-to-Peer Transfers```
How it Works:

Users add beneficiaries with account details
Select beneficiary and enter transfer amount
PIN verification for security
Amount deducted from sender's wallet
Amount added to receiver's wallet
Transaction recorded for both users


```Transaction History```
Features:

Complete transaction log for each user
Shows credits (add money) and debits (transfers)
Includes Razorpay reference IDs for payments
Real-time transaction status updates


```security Implementation```

4.5.1 Authentication Security
JWT Tokens: Secure session management
bcrypt Hashing: PIN and password protection
Rate Limiting: Brute force protection
Input Validation: SQL injection prevention
4.5.2 API Security
CORS Configuration: Cross-origin request control
Middleware Protection: Route-level authentication
Error Handling: Secure error responses
Data Sanitization: Input cleaning and validation


``5. Current Implementation Status``

5.1 Completed Features ✅
 User registration with biometric enrollment
 Face recognition authentication
 Voice recognition authentication
 OTP-based authentication
 JWT-based session management
 User dashboard with balance display
 Add money via Razorpay integration
 Peer-to-peer money transfers
 Beneficiary management
 Transaction history
 PIN-based security
 Responsive web design
 Database integration with Supabase


5.2 Key Achievements
Multi-Modal Authentication: Successfully implemented three different authentication methods
Real Banking Experience: Razorpay integration provides realistic payment flows
Accessibility Focus: Adaptive fusion approach accommodates deaf and dumb users
Security: Industry-standard security practices implemented
Scalability: Modular architecture supports future enhancements
5.3 Technical Innovations
Adaptive Fusion Strategy: User-centric approach to biometric fusion
Accessibility-First Design: Specifically designed for deaf and dumb users
Real-World Payment Integration: Razorpay test mode for realistic demos
Multi-Service Architecture: Separate Python AI service for biometric processing

6. Future Enhancements
6.1 Planned Features
Sign language recognition integration
Mobile application development
Advanced fraud detection
Real-time notifications
Multi-language support
6.2 Production Considerations
HTTPS implementation
Production database optimization
Razorpay live mode integration
Advanced monitoring and logging
Compliance with banking regulations

7. Learning Outcomes
7.1 Technical Skills Developed
Full-stack web development
Biometric system integration
Payment gateway implementation
Database design and management
API development and integration
Security best practices
7.2 Problem-Solving Approach
Identified accessibility challenges in traditional banking
Designed inclusive solutions using modern technology
Implemented adaptive authentication strategies
Created realistic banking simulation environment

8. Conclusion
This project successfully demonstrates the integration of multiple cutting-edge technologies to create an accessible banking solution. The combination of React.js frontend, Node.js backend, Python AI services, and Razorpay payment integration creates a comprehensive banking application that addresses the specific needs of deaf and dumb users while maintaining security and usability standards expected in financial applications.

The adaptive fusion approach to biometric authentication represents an innovative solution that prioritizes accessibility without compromising security, making this project a significant contribution to inclusive fintech solutions.
]