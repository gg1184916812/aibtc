# core/security/middleware.py
"""
Security middleware for input validation, rate limiting, and authentication
"""

import re
import logging
from functools import wraps
from flask import request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import jwt
from datetime import datetime, timedelta
from core.config import AppConfig

logger = logging.getLogger(__name__)

# Rate limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# JWT Secret Key
JWT_SECRET = AppConfig.SECRET_KEY
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24


class InputValidator:
    """Input validation utilities"""
    
    # Valid trading symbols pattern
    SYMBOL_PATTERN = re.compile(r'^[A-Z]{6,10}m?$')
    
    # Valid timeframes
    VALID_TIMEFRAMES = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1']
    
    # Valid model name pattern
    MODEL_NAME_PATTERN = re.compile(r'^[A-Za-z0-9_\-\.]+$')
    
    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """Validate trading symbol format"""
        if not symbol or not isinstance(symbol, str):
            return False
        return bool(InputValidator.SYMBOL_PATTERN.match(symbol))
    
    @staticmethod
    def validate_timeframe(timeframe: str) -> bool:
        """Validate timeframe"""
        return timeframe in InputValidator.VALID_TIMEFRAMES
    
    @staticmethod
    def validate_model_name(model_name: str) -> bool:
        """Validate model name format"""
        if not model_name or not isinstance(model_name, str):
            return False
        # Prevent path traversal
        if '..' in model_name or '/' in model_name or '\\' in model_name:
            return False
        return bool(InputValidator.MODEL_NAME_PATTERN.match(model_name))
    
    @staticmethod
    def validate_numeric_range(value, min_val=None, max_val=None) -> bool:
        """Validate numeric value within range"""
        try:
            num = float(value)
            if min_val is not None and num < min_val:
                return False
            if max_val is not None and num > max_val:
                return False
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_positive_number(value) -> bool:
        """Validate positive number"""
        return InputValidator.validate_numeric_range(value, min_val=0)


def validate_request_data(required_fields=None, optional_fields=None):
    """
    Decorator to validate request JSON data
    
    Args:
        required_fields: Dict of {field_name: (validator_func, error_message)}
        optional_fields: Dict of {field_name: (validator_func, error_message)}
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400
                
                # Validate required fields
                if required_fields:
                    for field, (validator, error_msg) in required_fields.items():
                        if field not in data:
                            return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
                        if not validator(data[field]):
                            return jsonify({'success': False, 'error': error_msg}), 400
                
                # Validate optional fields if present
                if optional_fields:
                    for field, (validator, error_msg) in optional_fields.items():
                        if field in data and data[field] is not None:
                            if not validator(data[field]):
                                return jsonify({'success': False, 'error': error_msg}), 400
                
                return f(*args, **kwargs)
            except Exception as e:
                logger.error(f"Request validation error: {e}")
                return jsonify({'success': False, 'error': 'Validation failed'}), 400
        return wrapped
    return decorator


def safe_error_handler(f):
    """
    Decorator to handle errors safely without exposing sensitive information
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"Validation error: {e}")
            return jsonify({'success': False, 'error': 'Invalid input data'}), 400
        except PermissionError as e:
            logger.warning(f"Permission error: {e}")
            return jsonify({'success': False, 'error': 'Permission denied'}), 403
        except FileNotFoundError as e:
            logger.warning(f"Resource not found: {e}")
            return jsonify({'success': False, 'error': 'Resource not found'}), 404
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return jsonify({'success': False, 'error': 'Internal server error'}), 500
    return wrapped


# JWT Authentication
def generate_token(user_id: str) -> str:
    """Generate JWT token"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None


def require_auth(f):
    """
    Decorator to require JWT authentication
    Note: This is a basic implementation. For production, use proper user management.
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Missing or invalid authorization header'}), 401
        
        token = auth_header.split(' ')[1]
        payload = verify_token(token)
        if not payload:
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401
        
        # Add user_id to request context
        request.user_id = payload.get('user_id')
        return f(*args, **kwargs)
    return wrapped


# For development: optional auth (can be disabled via config)
def optional_auth(f):
    """
    Decorator for optional JWT authentication
    If token is provided, it will be validated. If not, request proceeds as guest.
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            payload = verify_token(token)
            if payload:
                request.user_id = payload.get('user_id')
            else:
                return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401
        
        return f(*args, **kwargs)
    return wrapped
