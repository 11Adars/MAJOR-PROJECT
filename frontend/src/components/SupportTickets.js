import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './SupportTickets.css';

function SupportTickets() {
  const navigate = useNavigate();
  const [tickets, setTickets] = useState([]);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ total: 0, pending: 0, responded: 0, resolved: 0 });
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchTickets();
    fetchStats();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  const fetchTickets = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const config = {
        headers: { Authorization: `Bearer ${token}` },
        params: filter !== 'all' ? { status: filter } : {}
      };

      const response = await axios.get('http://127.0.0.1:5000/api/support/tickets', config);
      setTickets(response.data.tickets);
    } catch (error) {
      console.error('Error fetching tickets:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('http://127.0.0.1:5000/api/support/stats', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchTicketDetails = async (ticketId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`http://127.0.0.1:5000/api/support/tickets/${ticketId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSelectedTicket(response.data.ticket);
    } catch (error) {
      console.error('Error fetching ticket details:', error);
    }
  };

  const markAsResolved = async (ticketId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.patch(
        `http://127.0.0.1:5000/api/support/tickets/${ticketId}/resolve`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      fetchTickets();
      fetchStats();
      if (selectedTicket && selectedTicket.id === ticketId) {
        setSelectedTicket({ ...selectedTicket, status: 'resolved' });
      }
    } catch (error) {
      console.error('Error marking ticket as resolved:', error);
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      pending: { class: 'status-pending', icon: '🕐', text: 'Pending' },
      responded: { class: 'status-responded', icon: '✅', text: 'Responded' },
      resolved: { class: 'status-resolved', icon: '✔️', text: 'Resolved' }
    };
    const badge = badges[status] || badges.pending;
    return <span className={`status-badge ${badge.class}`}>{badge.icon} {badge.text}</span>;
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="support-tickets-container">
      <div className="support-header">
        <div className="header-left">
          <button onClick={() => navigate('/dashboard')} className="back-button">
            ← Back to Dashboard
          </button>
          <h1>Support Tickets</h1>
        </div>
        <button onClick={() => navigate('/sign-recognition')} className="new-ticket-btn">
          🤟 New Sign Language Query
        </button>
      </div>

      {/* Statistics Cards */}
      <div className="stats-grid">
        <div className="stat-card total">
          <div className="stat-icon">📊</div>
          <div className="stat-content">
            <span className="stat-label">Total Tickets</span>
            <span className="stat-value">{stats.total}</span>
          </div>
        </div>
        <div className="stat-card pending">
          <div className="stat-icon">🕐</div>
          <div className="stat-content">
            <span className="stat-label">Pending</span>
            <span className="stat-value">{stats.pending}</span>
          </div>
        </div>
        <div className="stat-card responded">
          <div className="stat-icon">✅</div>
          <div className="stat-content">
            <span className="stat-label">Responded</span>
            <span className="stat-value">{stats.responded}</span>
          </div>
        </div>
        <div className="stat-card resolved">
          <div className="stat-icon">✔️</div>
          <div className="stat-content">
            <span className="stat-label">Resolved</span>
            <span className="stat-value">{stats.resolved}</span>
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="filter-tabs">
        <button 
          className={`filter-tab ${filter === 'all' ? 'active' : ''}`}
          onClick={() => setFilter('all')}
        >
          All Tickets
        </button>
        <button 
          className={`filter-tab ${filter === 'pending' ? 'active' : ''}`}
          onClick={() => setFilter('pending')}
        >
          Pending
        </button>
        <button 
          className={`filter-tab ${filter === 'responded' ? 'active' : ''}`}
          onClick={() => setFilter('responded')}
        >
          Responded
        </button>
        <button 
          className={`filter-tab ${filter === 'resolved' ? 'active' : ''}`}
          onClick={() => setFilter('resolved')}
        >
          Resolved
        </button>
      </div>

      {/* Main Content */}
      <div className="tickets-main">
        {/* Tickets List */}
        <div className="tickets-list">
          {loading ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Loading tickets...</p>
            </div>
          ) : tickets.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📭</div>
              <h3>No Tickets Found</h3>
              <p>You haven't submitted any support queries yet.</p>
              <button onClick={() => navigate('/sign-recognition')} className="cta-button">
                Submit Your First Query
              </button>
            </div>
          ) : (
            tickets.map(ticket => (
              <div 
                key={ticket.id}
                className={`ticket-item ${selectedTicket?.id === ticket.id ? 'active' : ''}`}
                onClick={() => fetchTicketDetails(ticket.id)}
              >
                <div className="ticket-header">
                  <span className="ticket-id">Ticket #{ticket.id}</span>
                  {getStatusBadge(ticket.status)}
                </div>
                <div className="ticket-query">
                  {ticket.query_text.length > 100 
                    ? `${ticket.query_text.substring(0, 100)}...` 
                    : ticket.query_text}
                </div>
                <div className="ticket-meta">
                  <span className="ticket-source">
                    {ticket.query_source === 'sign_language' ? '🤟 Sign Language' : '💬 Manual'}
                  </span>
                  <span className="ticket-date">{formatDate(ticket.created_at)}</span>
                  {ticket.response_count > 0 && (
                    <span className="response-count">
                      💬 {ticket.response_count} {ticket.response_count === 1 ? 'Response' : 'Responses'}
                    </span>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Ticket Details */}
        <div className="ticket-details">
          {selectedTicket ? (
            <div className="details-content">
              <div className="details-header">
                <h2>Ticket #{selectedTicket.id}</h2>
                {getStatusBadge(selectedTicket.status)}
              </div>

              <div className="details-section">
                <h3>Your Query</h3>
                <div className="query-box">
                  <p>{selectedTicket.query_text}</p>
                </div>
                <div className="details-meta">
                  <span>Submitted: {formatDate(selectedTicket.created_at)}</span>
                  {selectedTicket.query_source === 'sign_language' && (
                    <span className="sign-badge">🤟 Generated via Sign Language</span>
                  )}
                </div>
              </div>

              {selectedTicket.responses && selectedTicket.responses.length > 0 && (
                <div className="details-section">
                  <h3>Responses ({selectedTicket.responses.length})</h3>
                  <div className="responses-list">
                    {selectedTicket.responses.map((response, index) => (
                      <div key={response.id} className="response-item">
                        <div className="response-header">
                          <span className="response-from">
                            🏦 Bank Support
                          </span>
                          <span className="response-date">
                            {formatDate(response.created_at)}
                          </span>
                        </div>
                        <div className="response-text">
                          {response.response_text}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {selectedTicket.status !== 'resolved' && (
                <div className="details-actions">
                  {selectedTicket.responses && selectedTicket.responses.length > 0 && (
                    <button 
                      onClick={() => markAsResolved(selectedTicket.id)}
                      className="resolve-button"
                    >
                      ✔️ Mark as Resolved
                    </button>
                  )}
                  {(!selectedTicket.responses || selectedTicket.responses.length === 0) && (
                    <div className="waiting-message">
                      <p>⏳ Waiting for bank support to respond...</p>
                      <p className="note">You'll receive an email notification when they reply.</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="no-selection">
              <div className="no-selection-icon">📄</div>
              <h3>Select a Ticket</h3>
              <p>Click on a ticket from the list to view details and responses</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default SupportTickets;
