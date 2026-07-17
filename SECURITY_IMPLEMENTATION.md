# Security Implementation Guide

## Overview
This document describes the security enhancements implemented for QuantumBotX.

## Implemented Security Features

### 1. SQL Injection Prevention
**File**: `core/db/queries.py:156`
- Fixed parameterized query construction
- Changed from f-string to proper parameter binding
- Prevents SQL injection attacks

### 2. Thread Safety for Global State
**File**: `core/routes/api_ai_predictor.py`
- Added `_training_lock` for training status
- Added `_backtest_lock` for backtest status
- All status updates now protected with locks
- Prevents race conditions in concurrent requests

### 3. Input Validation Middleware
**File**: `core/security/middleware.py`

#### InputValidator Class
```python
from core.security.middleware import InputValidator

# Validate trading symbol
if not InputValidator.validate_symbol(symbol):
    return error("Invalid symbol format")

# Validate timeframe
if not InputValidator.validate_timeframe(timeframe):
    return error("Invalid timeframe")

# Validate model name (prevents path traversal)
if not InputValidator.validate_model_name(model_name):
    return error("Invalid model name")

# Validate numeric ranges
if not InputValidator.validate_numeric_range(risk, min_val=0, max_val=5):
    return error("Risk must be between 0 and 5")
```

#### Validation Decorator
```python
from core.security.middleware import validate_request_data

@api.route('/train', methods=['POST'])
@validate_request_data(
    required_fields={
        'symbol': (InputValidator.validate_symbol, "Invalid symbol format"),
        'timeframe': (InputValidator.validate_timeframe, "Invalid timeframe")
    },
    optional_fields={
        'epochs': (lambda x: InputValidator.validate_numeric_range(x, min_val=10, max_val=500), "Epochs must be 10-500")
    }
)
def train():
    # Your code here
    pass
```

### 4. Rate Limiting
**File**: `requirements.txt`
- Added Flask-Limiter>=3.5.0
- Default limits: 200 requests/day, 50 requests/hour per IP

**Usage**:
```python
from core.security.middleware import limiter

@api.route('/sensitive-endpoint', methods=['POST'])
@limiter.limit("10 per minute")
def sensitive_operation():
    pass
```

### 5. Safe Error Handling
**File**: `core/security/middleware.py`

```python
from core.security.middleware import safe_error_handler

@api.route('/endpoint', methods=['POST'])
@safe_error_handler
def endpoint():
    # Errors are caught and sanitized
    # No sensitive information leaked to clients
    pass
```

### 6. JWT Authentication
**Files**: 
- `core/security/middleware.py` (JWT functions)
- `core/security/auth.py` (User management)
- `core/routes/api_auth.py` (Auth endpoints)

#### Login Endpoint
```bash
POST /api/auth/login
Content-Type: application/json

{
    "username": "admin",
    "password": "admin123"
}
```

Response:
```json
{
    "success": true,
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
        "username": "admin",
        "role": "admin"
    }
}
```

#### Protecting Endpoints
```python
from core.security.middleware import require_auth

@api.route('/train', methods=['POST'])
@require_auth
def train():
    # Only accessible with valid JWT token
    user_id = request.user_id
    pass
```

#### Optional Authentication
```python
from core.security.middleware import optional_auth

@api.route('/public-data', methods=['GET'])
@optional_auth
def public_data():
    # Works with or without token
    if hasattr(request, 'user_id'):
        # Authenticated user
        pass
    else:
        # Guest user
        pass
```

#### Using Token in Requests
```bash
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     -X POST \
     http://localhost:5001/api/ai-predictor/train
```

## Installation

1. Install new dependencies:
```bash
pip install Flask-Limiter>=3.5.0 PyJWT>=2.8.0
```

2. Register the auth blueprint in your Flask app:
```python
from core.routes.api_auth import api_auth

app.register_blueprint(api_auth)
```

3. Initialize rate limiter:
```python
from core.security.middleware import limiter

limiter.init_app(app)
```

## Security Best Practices

### For Development
- Default admin user: `admin` / `admin123`
- **CHANGE THIS IN PRODUCTION!**
- JWT tokens expire after 24 hours

### For Production
1. **Change default credentials**
   - Edit `core/security/auth.py`
   - Use strong passwords
   - Consider using bcrypt instead of SHA-256

2. **Use environment variables for secrets**
   ```python
   # In core/config.py
   JWT_SECRET = os.getenv('JWT_SECRET', secrets.token_hex(32))
   ```

3. **Enable HTTPS**
   - Never use JWT over HTTP
   - Use TLS/SSL in production

4. **Implement proper user management**
   - Store users in database
   - Add password reset functionality
   - Implement role-based access control

5. **Add CSRF protection**
   - Use Flask-WTF for form validation
   - Implement CSRF tokens for state-changing requests

6. **Enable logging and monitoring**
   - Log all authentication attempts
   - Monitor for suspicious activity
   - Set up alerts for failed login attempts

## Applying Security to Existing Endpoints

### Example: Securing Training Endpoint
```python
from core.security.middleware import require_auth, validate_request_data, InputValidator, safe_error_handler

@api_ai_predictor.route('/train', methods=['POST'])
@require_auth
@validate_request_data(
    required_fields={
        'symbol': (InputValidator.validate_symbol, "Invalid symbol format"),
        'timeframe': (InputValidator.validate_timeframe, "Invalid timeframe")
    }
)
@safe_error_handler
@limiter.limit("5 per hour")
def train():
    # Your existing training code
    pass
```

## Testing Security

### Test Authentication
```python
import requests

# Login
response = requests.post('http://localhost:5001/api/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})
token = response.json()['token']

# Use token
headers = {'Authorization': f'Bearer {token}'}
response = requests.post('http://localhost:5001/api/ai-predictor/train', 
                        json={'symbol': 'XAUUSDm', 'timeframe': 'H1'},
                        headers=headers)
```

### Test Rate Limiting
```python
# Make 51 requests quickly
for i in range(51):
    response = requests.get('http://localhost:5001/api/ai-predictor/models')
    if response.status_code == 429:
        print("Rate limit hit!")
        break
```

### Test Input Validation
```python
# Invalid symbol
response = requests.post('http://localhost:5001/api/ai-predictor/train',
                        json={'symbol': '../../../etc/passwd', 'timeframe': 'H1'})
# Should return 400 with validation error
```

## Future Enhancements

1. **Replace pickle with joblib** - Safer model serialization
2. **Add database-backed user management** - Proper user storage
3. **Implement OAuth2** - Third-party authentication
4. **Add 2FA** - Two-factor authentication
5. **API key management** - For programmatic access
6. **Audit logging** - Track all sensitive operations
7. **IP whitelisting** - Restrict access by IP
8. **Request signing** - Additional request integrity

## Troubleshooting

### Import Errors
If you get import errors for security modules:
```python
# Make sure core/security/__init__.py exists
# Check that core is in your Python path
```

### Rate Limiting Issues
If rate limiting is too strict:
```python
# Adjust limits in core/security/middleware.py
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["500 per day", "100 per hour"],  # Increased limits
    storage_uri="memory://"
)
```

### JWT Token Issues
If tokens expire too quickly:
```python
# Adjust in core/security/middleware.py
JWT_EXPIRATION_HOURS = 48  # Increase to 48 hours
```

## Support

For security issues or questions, please:
1. Check this documentation first
2. Review the code comments in security modules
3. Test in development environment first
4. Report security vulnerabilities responsibly
