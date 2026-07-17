# core/security/auth.py
"""
Simple authentication system for development
For production, replace with proper user management system
"""

import hashlib
import secrets
from typing import Optional, Dict
from core.db.connection import get_db_connection
import logging

logger = logging.getLogger(__name__)


class SimpleAuth:
    """Simple in-memory authentication for development"""
    
    def __init__(self):
        # Default admin user (change in production!)
        self.users = {
            'admin': {
                'password_hash': self._hash_password('admin123'),
                'role': 'admin'
            }
        }
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash password using SHA-256 (use bcrypt in production)"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, username: str, password: str) -> bool:
        """Verify user credentials"""
        user = self.users.get(username)
        if not user:
            return False
        return user['password_hash'] == self._hash_password(password)
    
    def create_user(self, username: str, password: str, role: str = 'user') -> bool:
        """Create a new user"""
        if username in self.users:
            return False
        self.users[username] = {
            'password_hash': self._hash_password(password),
            'role': role
        }
        return True
    
    def get_user_role(self, username: str) -> Optional[str]:
        """Get user role"""
        user = self.users.get(username)
        return user['role'] if user else None


# Global auth instance
auth = SimpleAuth()


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """
    Authenticate user and return user info if successful
    
    Returns:
        Dict with user info if successful, None otherwise
    """
    if auth.verify_password(username, password):
        return {
            'username': username,
            'role': auth.get_user_role(username)
        }
    return None


def create_api_token(username: str) -> str:
    """Generate a simple API token for user"""
    # In production, use proper JWT tokens
    token_data = f"{username}:{secrets.token_hex(16)}"
    return hashlib.sha256(token_data.encode()).hexdigest()


def init_default_users():
    """Initialize default users for development"""
    logger.info("Initializing default authentication users")
    logger.warning("Default admin user: admin / admin123 (CHANGE IN PRODUCTION!)")
