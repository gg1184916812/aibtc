# core/routes/api_auth.py
"""
Authentication API routes
"""

from flask import Blueprint, request, jsonify
from core.security.middleware import generate_token, InputValidator
from core.security.auth import authenticate_user, init_default_users
import logging

logger = logging.getLogger(__name__)

api_auth = Blueprint('api_auth', __name__, url_prefix='/api/auth')

# Initialize default users on module load
init_default_users()


@api_auth.route('/login', methods=['POST'])
def login():
    """
    User login endpoint
    
    Request body:
    {
        "username": "admin",
        "password": "admin123"
    }
    
    Response:
    {
        "success": true,
        "token": "jwt_token_here",
        "user": {
            "username": "admin",
            "role": "admin"
        }
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid request'}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Basic validation
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password required'}), 400
        
        # Authenticate
        user_info = authenticate_user(username, password)
        if not user_info:
            logger.warning(f"Failed login attempt for user: {username}")
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        # Generate JWT token
        token = generate_token(user_info['username'])
        
        logger.info(f"User logged in: {username}")
        
        return jsonify({
            'success': True,
            'token': token,
            'user': user_info
        })
    
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Login failed'}), 500


@api_auth.route('/verify', methods=['POST'])
def verify():
    """
    Verify JWT token
    
    Request headers:
    Authorization: Bearer <token>
    
    Response:
    {
        "success": true,
        "valid": true,
        "user": {
            "user_id": "admin"
        }
    }
    """
    from core.security.middleware import verify_token
    
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Missing authorization header'}), 400
        
        token = auth_header.split(' ')[1]
        payload = verify_token(token)
        
        if not payload:
            return jsonify({'success': False, 'valid': False, 'error': 'Invalid or expired token'}), 401
        
        return jsonify({
            'success': True,
            'valid': True,
            'user': {
                'user_id': payload.get('user_id')
            }
        })
    
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return jsonify({'success': False, 'error': 'Verification failed'}), 500
