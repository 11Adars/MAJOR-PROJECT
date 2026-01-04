const Imap = require('imap');
const { simpleParser } = require('mailparser');
const pool = require('../db');
const { notifyUserOfResponse } = require('../utils/emailService');
require('dotenv').config();

class EmailPollingService {
  constructor() {
    this.imap = null;
    this.isRunning = false;
    this.pollInterval =20*60*1000;
    this.checkInterval = null;
  }

  // Initialize IMAP connection
  initializeImap() {
    // Connect to BANK support email to check for replies
    const bankEmail = process.env.BANK_SUPPORT_EMAIL;
    const bankPassword = process.env.BANK_EMAIL_PASS || process.env.EMAIL_PASS;
    
    if (!bankEmail || !bankPassword) {
      throw new Error('BANK_SUPPORT_EMAIL and BANK_EMAIL_PASS must be set in .env');
    }

    this.imap = new Imap({
      user: bankEmail,
      password: bankPassword,
      host: process.env.EMAIL_IMAP_HOST || 'imap.gmail.com',
      port: process.env.EMAIL_IMAP_PORT || 993,
      tls: true,
      tlsOptions: { rejectUnauthorized: false },
      authTimeout: 10000,
      connTimeout: 10000
    });

    this.imap.once('error', (err) => {
      console.error('IMAP connection error:', err.message);
      // Don't reconnect immediately, let scheduled check handle it
    });

    this.imap.once('end', () => {
      console.log('IMAP connection ended');
      // Connection will be recreated on next scheduled check
    });
  }

  // Reconnect after error (not used anymore, but kept for compatibility)
  reconnect() {
    console.log('⚠️ Connection error - will retry on next scheduled check');
    // Don't try to reconnect immediately, let the scheduled interval handle it
  }

  // Extract ticket ID from subject line
  extractTicketId(subject) {
    // Match patterns like:
    // - "Re: Support Query - Ticket #123"
    // - "Re: Support Query #11 from Adarsh"
    // - "Support Query #11"
    const match = subject.match(/#(\d+)/i);  // Match any #followed by digits
    return match ? parseInt(match[1]) : null;
  }

  // Process a single email message
  async processEmail(seqno, msg) {
    return new Promise((resolve, reject) => {
      const parsed = simpleParser(msg);
      
      parsed.then(async (mail) => {
        try {
          console.log(`\n📧 Processing Email ${seqno}:`);
          console.log(`   Subject: "${mail.subject}"`);
          console.log(`   From: ${mail.from?.text || mail.from?.value?.[0]?.address}`);
          console.log(`   To: ${mail.to?.text || mail.to?.value?.[0]?.address}`);
          
          const ticketId = this.extractTicketId(mail.subject);
          
          if (!ticketId) {
            console.log(`   ❌ No ticket ID found in subject`);
            return resolve();
          }

          console.log(`   ✅ Found Ticket ID: #${ticketId}`);

          // Check if ticket exists
          const ticketResult = await pool.query(
            'SELECT id, user_id, user_email, status FROM support_tickets WHERE id = $1',
            [ticketId]
          );

          if (ticketResult.rows.length === 0) {
            console.log(`   ❌ Ticket #${ticketId} not found in database`);
            return resolve();
          }

          const ticket = ticketResult.rows[0];
          console.log(`   📋 Ticket Status: ${ticket.status}`);

          // Check if ticket already has a response (skip if already responded)
          if (ticket.status === 'responded' || ticket.status === 'resolved') {
            console.log(`   ⏭️  Ticket already ${ticket.status} - skipping`);
            return resolve();
          }

          // Extract response text (clean up quoted text)
          let responseText = mail.text || mail.html?.replace(/<[^>]*>/g, '');
          
          console.log(`   📝 Raw text length: ${responseText?.length || 0} characters`);
          
          // Remove quoted text (lines starting with >)
          responseText = responseText
            .split('\n')
            .filter(line => !line.trim().startsWith('>'))
            .join('\n')
            .trim();

          // Remove email signatures and footers
          const signatureMarkers = ['--', 'Sent from', 'Best regards', 'Thanks', 'Thank you'];
          for (const marker of signatureMarkers) {
            const index = responseText.indexOf(marker);
            if (index > 0) {
              responseText = responseText.substring(0, index).trim();
            }
          }

          // Limit response length
          if (responseText.length > 2000) {
            responseText = responseText.substring(0, 2000) + '...';
          }

          console.log(`   📝 Cleaned text length: ${responseText?.length || 0} characters`);
          console.log(`   📝 Preview: "${responseText?.substring(0, 100)}..."`);

          if (!responseText || responseText.length < 10) {
            console.log(`   ❌ Response text too short or empty (need at least 10 chars)`);
            return resolve();
          }

          // Check if this response already exists (avoid duplicates)
          const existingResponse = await pool.query(
            'SELECT id FROM ticket_responses WHERE ticket_id = $1 AND response_text = $2',
            [ticketId, responseText]
          );

          if (existingResponse.rows.length > 0) {
            console.log(`   ⏭️  Response already exists in database`);
            return resolve();
          }

          console.log(`   ✅ Response is new, adding to database...`);

          // Insert response into database
          const insertResult = await pool.query(
            `INSERT INTO ticket_responses (ticket_id, response_text, response_from, created_at)
             VALUES ($1, $2, $3, NOW()) RETURNING id`,
            [ticketId, responseText, 'Bank Support']
          );
          console.log(`   ✅ Response inserted with ID: ${insertResult.rows[0].id}`);

          // Update ticket status
          await pool.query(
            `UPDATE support_tickets 
             SET status = 'responded', updated_at = NOW() 
             WHERE id = $1`,
            [ticketId]
          );
          console.log(`   ✅ Ticket #${ticketId} status updated to 'responded'`);

          console.log(`\n✅✅ SUCCESS: Email ${seqno} - Added response to ticket #${ticketId} ✅✅\n`);

          // Send notification to user
          try {
            await notifyUserOfResponse(
              ticket.user_email,
              ticketId,
              responseText
            );
            console.log(`   📧 Notification sent to ${ticket.user_email}`);
          } catch (emailError) {
            console.error(`   ⚠️  Failed to send notification:`, emailError.message);
          }

          // Mark email as read
          this.imap.addFlags(seqno, ['\\Seen'], (err) => {
            if (err) console.error('Error marking email as read:', err);
          });

          resolve();
        } catch (error) {
          console.error(`Error processing email ${seqno}:`, error);
          reject(error);
        }
      }).catch(reject);
    });
  }

  // Check for new replies in inbox
  checkForReplies() {
    // Create fresh IMAP connection each time
    this.imap = null;
    this.initializeImap();

    this.imap.once('ready', () => {
      console.log('📬 Checking for email replies...');

      // Add small delay to ensure connection is fully ready
      setTimeout(() => {
        // Check SENT folder for bank's replies (not INBOX)
        this.imap.openBox('[Gmail]/Sent Mail', false, (err, box) => {
          if (err) {
            console.error('Error opening Sent folder:', err);
            console.log('Trying alternative Sent folder name...');
            // Try alternative sent folder name
            this.imap.openBox('Sent', false, (err2, box2) => {
              if (err2) {
                console.error('Error opening Sent folder (alternative):', err2);
                this.imap.end();
                return;
              }
              this.searchSentEmails();
            });
            return;
          }

          console.log('✅ Sent Mail folder opened successfully');
          this.searchSentEmails();
        });
      }, 1000); // Wait 1 second after 'ready' event
    });

    this.imap.once('error', (err) => {
      console.error('IMAP error during check:', err.message);
      // Don't call reconnect here, just let the next scheduled check happen
    });

    try {
      this.imap.connect();
    } catch (err) {
      console.error('Error connecting to IMAP:', err.message);
    }
  }

  // Search sent emails for bank replies
  searchSentEmails() {
    // First, let's search for ALL recent emails to see what we have
    console.log('🔍 Searching Sent folder for recent emails...');
    
    this.imap.search(['ALL'], (err, results) => {
      if (err) {
        console.error('Error searching emails:', err);
        this.imap.end();
        return;
      }

      if (!results || results.length === 0) {
        console.log('❌ No emails found in Sent folder at all');
        this.imap.end();
        return;
      }

      console.log(`📧 Found ${results.length} total sent email(s), checking for ticket references...`);

      // Fetch last 5 emails to check their subjects
      const recentEmails = results.slice(-5);
      const emailsToProcess = [];
      const emailMap = new Map(); // Map seqno to UID
      
      const headerFetch = this.imap.fetch(recentEmails, { 
        bodies: 'HEADER.FIELDS (SUBJECT TO)',
        struct: false
      });

      headerFetch.on('message', (msg, seqno) => {
        let emailUid = null;
        let headerBuffer = '';
        
        // Capture the UID from attributes FIRST
        msg.once('attributes', (attrs) => {
          emailUid = attrs.uid;
          emailMap.set(seqno, emailUid);
        });
        
        msg.on('body', (stream, info) => {
          stream.on('data', (chunk) => {
            headerBuffer += chunk.toString('utf8');
          });
        });
        
        // Process AFTER all data is received
        msg.once('end', () => {
          // Now we have both UID and header data
          const subjectMatch = headerBuffer.match(/Subject: (.*)/i);
          const toMatch = headerBuffer.match(/To: (.*)/i);
          
          if (subjectMatch) {
            const subject = subjectMatch[1].trim();
            const to = toMatch ? toMatch[1].trim() : '';
            const uid = emailMap.get(seqno) || emailUid;
            
            console.log(`Email ${seqno} (UID: ${uid}): "${subject.substring(0, 60)}..."`);
            
            // Check if it's a reply to a support query (has Ticket # or Re:)
            if (subject.includes('Ticket #') || subject.includes('Re:')) {
              console.log(`  ✅ Has ticket reference - will process (UID: ${uid})`);
              if (uid) {
                emailsToProcess.push(uid);
              } else {
                console.warn(`  ⚠️  UID still not available for seqno ${seqno}`);
              }
            } else {
              console.log(`  ⏭️  No ticket reference - skipping`);
            }
          }
        });
      });

      headerFetch.once('error', (err) => {
        console.error('Header fetch error:', err);
        this.imap.end();
      });

      headerFetch.once('end', () => {
        if (emailsToProcess.length === 0) {
          console.log('❌ No emails with ticket references found');
          this.imap.end();
          return;
        }

        console.log(`\n✅ Processing ${emailsToProcess.length} email(s) with ticket references...`);
        console.log(`   Fetching full bodies for UIDs: ${emailsToProcess.join(', ')}`);

        // Fetch full bodies using UIDs - THIS IS CRITICAL!
        const bodyFetch = this.imap.fetch(emailsToProcess, { 
          bodies: '',  // Empty string means fetch entire RFC822 message
          struct: true,
          markSeen: false
        });
        let processedCount = 0;
        let messagesStarted = 0;

        bodyFetch.on('message', (msg, seqno) => {
          messagesStarted++;
          console.log(`\n📨 Message event fired for email ${seqno} (${messagesStarted}/${emailsToProcess.length})`);
          
          msg.on('body', (stream, info) => {
            console.log(`   📥 Body stream started for email ${seqno}, info:`, info);
            processedCount++;
            
            this.processEmail(seqno, stream)
              .then(() => {
                console.log(`   ✅ Finished processing email ${seqno}`);
              })
              .catch(err => {
                console.error(`   ❌ Error processing email ${seqno}:`, err.message);
                console.error(err.stack);
              });
          });
          
          msg.once('attributes', (attrs) => {
            console.log(`   📋 Attributes received for email ${seqno}, uid: ${attrs.uid}`);
          });
        });

        bodyFetch.once('error', (err) => {
          console.error('❌ Body fetch error:', err);
          this.imap.end();
        });

        bodyFetch.once('end', () => {
          console.log(`\n✅ Body fetch 'end' event fired`);
          console.log(`   Messages started: ${messagesStarted}/${emailsToProcess.length}`);
          console.log(`   Bodies processed: ${processedCount}`);
          
          if (messagesStarted === 0) {
            console.error(`\n⚠️⚠️  WARNING: No 'message' events fired during body fetch!`);
            console.error(`   This usually means:`);
            console.error(`   1. The sequence numbers don't exist`);
            console.error(`   2. The IMAP connection was closed`);
            console.error(`   3. The fetch parameters are incorrect`);
          }
          
          // Give time for async processing to complete before closing
          setTimeout(() => {
            console.log('🔚 Closing IMAP connection');
            this.imap.end();
          }, 2000);
        });
      });
    });
  }

  // Start the polling service
  start() {
    if (this.isRunning) {
      console.log('Email polling service is already running');
      return;
    }

    console.log('🚀 Starting email polling service...');
    console.log(`📧 Monitoring BANK email: ${process.env.BANK_SUPPORT_EMAIL}`);
    console.log(`⏱️  Poll interval: ${this.pollInterval / 1000 / 60} minutes`);

    this.isRunning = true;

    // Check immediately on start
    this.checkForReplies();

    // Then check at regular intervals
    this.checkInterval = setInterval(() => {
      this.checkForReplies();
    }, this.pollInterval);

    console.log('✅ Email polling service started');
  }

  // Stop the polling service
  stop() {
    console.log('🛑 Stopping email polling service...');
    this.isRunning = false;

    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }

    if (this.imap) {
      this.imap.end();
      this.imap = null;
    }

    console.log('✅ Email polling service stopped');
  }

  // Get service status
  getStatus() {
    return {
      running: this.isRunning,
      email: process.env.EMAIL_USER,
      pollInterval: this.pollInterval / 1000 / 60 + ' minutes',
      lastCheck: new Date().toISOString()
    };
  }
}

// Create singleton instance
const emailPollingService = new EmailPollingService();

module.exports = emailPollingService;
