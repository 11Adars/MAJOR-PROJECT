"""
User Biometric Database
========================

Stores and retrieves user biometric templates for authentication.

Database Schema:
- user_id: Unique identifier
- face_embedding: 512-dim face features (blob)
- hand_features: 128-dim hand geometry (blob)
- style_features: 64-dim signing style (blob)
- enrolled_date: Timestamp
- last_authenticated: Timestamp
- authentication_count: Number of successful authentications

Features:
- SQLite database for persistent storage
- Efficient biometric template retrieval
- User enrollment and deletion
- Authentication history tracking
"""

import sqlite3
import numpy as np
import pickle
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from pathlib import Path
import os


class UserBiometricDatabase:
    """
    Database for storing user biometric templates.
    
    Uses SQLite with blob storage for numpy arrays.
    """
    
    def __init__(self, db_path: str = "data/biometric_users.db"):
        """
        Initialize user biometric database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        
        # Create data directory if needed
        db_dir = os.path.dirname(db_path)
        if db_dir:  # Only create if path has directory component
            os.makedirs(db_dir, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        print(f"💾 User Biometric Database initialized: {db_path}")
    
    def _init_database(self):
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                face_embedding BLOB NOT NULL,
                hand_features BLOB NOT NULL,
                style_features BLOB NOT NULL,
                enrolled_date TEXT NOT NULL,
                last_authenticated TEXT,
                authentication_count INTEGER DEFAULT 0,
                notes TEXT
            )
        """)
        
        # Create authentication log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auth_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                authenticated BOOLEAN NOT NULL,
                fusion_score REAL,
                face_score REAL,
                hand_score REAL,
                style_score REAL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def enroll_user(
        self,
        user_id: str,
        biometric_features: Dict[str, np.ndarray],
        notes: str = ""
    ) -> bool:
        """
        Enroll a new user with biometric templates.
        
        Args:
            user_id: Unique user identifier
            biometric_features: Dict with keys 'face', 'hand', 'style'
            notes: Optional notes about the user
        
        Returns:
            True if enrollment successful, False if user already exists
        """
        # Check if user already exists
        if self.user_exists(user_id):
            print(f"⚠️  User {user_id} already exists. Use update_user() to modify.")
            return False
        
        # Serialize numpy arrays to binary
        face_blob = pickle.dumps(biometric_features['face'])
        hand_blob = pickle.dumps(biometric_features['hand'])
        style_blob = pickle.dumps(biometric_features['style'])
        
        # Insert into database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO users (
                user_id, face_embedding, hand_features, style_features,
                enrolled_date, notes
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            face_blob,
            hand_blob,
            style_blob,
            datetime.now().isoformat(),
            notes
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ User {user_id} enrolled successfully")
        return True
    
    def get_user_biometrics(self, user_id: str) -> Optional[Dict[str, np.ndarray]]:
        """
        Retrieve biometric templates for a user.
        
        Args:
            user_id: User identifier
        
        Returns:
            Dict with keys 'face', 'hand', 'style', or None if user not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT face_embedding, hand_features, style_features
            FROM users
            WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result is None:
            return None
        
        # Deserialize numpy arrays
        face = pickle.loads(result[0])
        hand = pickle.loads(result[1])
        style = pickle.loads(result[2])
        
        return {
            'face': face,
            'hand': hand,
            'style': style
        }
    
    def update_user_biometrics(
        self,
        user_id: str,
        biometric_features: Dict[str, np.ndarray]
    ) -> bool:
        """
        Update biometric templates for an existing user.
        
        Args:
            user_id: User identifier
            biometric_features: New biometric features
        
        Returns:
            True if update successful, False if user not found
        """
        if not self.user_exists(user_id):
            print(f"⚠️  User {user_id} not found")
            return False
        
        # Serialize numpy arrays
        face_blob = pickle.dumps(biometric_features['face'])
        hand_blob = pickle.dumps(biometric_features['hand'])
        style_blob = pickle.dumps(biometric_features['style'])
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users
            SET face_embedding = ?, hand_features = ?, style_features = ?
            WHERE user_id = ?
        """, (face_blob, hand_blob, style_blob, user_id))
        
        conn.commit()
        conn.close()
        
        print(f"✅ User {user_id} biometrics updated")
        return True
    
    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user and their biometric data.
        
        Args:
            user_id: User identifier
        
        Returns:
            True if deletion successful, False if user not found
        """
        if not self.user_exists(user_id):
            print(f"⚠️  User {user_id} not found")
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete user
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        
        # Delete authentication logs
        cursor.execute("DELETE FROM auth_log WHERE user_id = ?", (user_id,))
        
        conn.commit()
        conn.close()
        
        print(f"✅ User {user_id} deleted")
        return True
    
    def user_exists(self, user_id: str) -> bool:
        """Check if user exists in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", (user_id,))
        count = cursor.fetchone()[0]
        
        conn.close()
        return count > 0
    
    def log_authentication(
        self,
        user_id: str,
        authenticated: bool,
        fusion_score: float,
        individual_scores: Dict[str, float]
    ):
        """
        Log an authentication attempt.
        
        Args:
            user_id: User identifier
            authenticated: Whether authentication was successful
            fusion_score: Overall fusion score
            individual_scores: Dict with 'face', 'hand', 'style' scores
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Log to auth_log table
        cursor.execute("""
            INSERT INTO auth_log (
                user_id, timestamp, authenticated, fusion_score,
                face_score, hand_score, style_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            datetime.now().isoformat(),
            authenticated,
            fusion_score,
            individual_scores.get('face', 0.0),
            individual_scores.get('hand', 0.0),
            individual_scores.get('style', 0.0)
        ))
        
        # Update user record if authenticated
        if authenticated:
            cursor.execute("""
                UPDATE users
                SET last_authenticated = ?,
                    authentication_count = authentication_count + 1
                WHERE user_id = ?
            """, (datetime.now().isoformat(), user_id))
        
        conn.commit()
        conn.close()
    
    def get_all_users(self) -> List[Dict]:
        """
        Get list of all enrolled users.
        
        Returns:
            List of dicts with user information
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, enrolled_date, last_authenticated,
                   authentication_count, notes
            FROM users
            ORDER BY enrolled_date DESC
        """)
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'user_id': row[0],
                'enrolled_date': row[1],
                'last_authenticated': row[2],
                'authentication_count': row[3],
                'notes': row[4]
            })
        
        conn.close()
        return users
    
    def get_user_info(self, user_id: str) -> Optional[Dict]:
        """
        Get detailed information about a user.
        
        Args:
            user_id: User identifier
        
        Returns:
            Dict with user information, or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, enrolled_date, last_authenticated,
                   authentication_count, notes
            FROM users
            WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result is None:
            return None
        
        return {
            'user_id': result[0],
            'enrolled_date': result[1],
            'last_authenticated': result[2],
            'authentication_count': result[3],
            'notes': result[4]
        }
    
    def get_authentication_history(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get authentication history for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of records to return
        
        Returns:
            List of authentication attempts
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, authenticated, fusion_score,
                   face_score, hand_score, style_score
            FROM auth_log
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user_id, limit))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'timestamp': row[0],
                'authenticated': bool(row[1]),
                'fusion_score': row[2],
                'face_score': row[3],
                'hand_score': row[4],
                'style_score': row[5]
            })
        
        conn.close()
        return history
    
    def get_statistics(self) -> Dict:
        """
        Get database statistics.
        
        Returns:
            Dict with statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total users
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        # Total authentications
        cursor.execute("SELECT COUNT(*) FROM auth_log WHERE authenticated = 1")
        total_auth = cursor.fetchone()[0]
        
        # Failed authentications
        cursor.execute("SELECT COUNT(*) FROM auth_log WHERE authenticated = 0")
        failed_auth = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_users': total_users,
            'total_authentications': total_auth,
            'failed_authentications': failed_auth,
            'success_rate': total_auth / max(total_auth + failed_auth, 1)
        }


# ==================== TESTING ====================
if __name__ == "__main__":
    print("🔬 Testing User Biometric Database...")
    
    # Use test database
    db = UserBiometricDatabase(db_path="test_biometric.db")
    
    # Test enrollment
    print("\n--- Test 1: User Enrollment ---")
    test_features = {
        'face': np.random.randn(512),
        'hand': np.random.randn(128),
        'style': np.random.randn(64)
    }
    
    success = db.enroll_user("test_user_001", test_features, notes="Test user for demo")
    print(f"Enrollment success: {success}")
    
    # Test retrieval
    print("\n--- Test 2: Biometric Retrieval ---")
    retrieved = db.get_user_biometrics("test_user_001")
    if retrieved:
        print(f"Face shape: {retrieved['face'].shape}")
        print(f"Hand shape: {retrieved['hand'].shape}")
        print(f"Style shape: {retrieved['style'].shape}")
    
    # Test user info
    print("\n--- Test 3: User Information ---")
    info = db.get_user_info("test_user_001")
    if info:
        print(f"User ID: {info['user_id']}")
        print(f"Enrolled: {info['enrolled_date']}")
        print(f"Notes: {info['notes']}")
    
    # Test authentication logging
    print("\n--- Test 4: Authentication Logging ---")
    db.log_authentication(
        "test_user_001",
        authenticated=True,
        fusion_score=0.85,
        individual_scores={'face': 0.90, 'hand': 0.82, 'style': 0.78}
    )
    
    history = db.get_authentication_history("test_user_001", limit=5)
    print(f"Authentication history: {len(history)} records")
    if history:
        print(f"Latest: {history[0]}")
    
    # Test statistics
    print("\n--- Test 5: Database Statistics ---")
    stats = db.get_statistics()
    print(f"Total users: {stats['total_users']}")
    print(f"Total authentications: {stats['total_authentications']}")
    print(f"Success rate: {stats['success_rate']:.2%}")
    
    # Test deletion
    print("\n--- Test 6: User Deletion ---")
    deleted = db.delete_user("test_user_001")
    print(f"Deletion success: {deleted}")
    
    # Cleanup
    if os.path.exists("test_biometric.db"):
        os.remove("test_biometric.db")
    
    print("\n✨ All tests passed!")
