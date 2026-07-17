# core/routes/api_strategy_switcher.py
"""
API Strategy Switcher Module
Handles strategy switching API endpoints
"""

# Fix import error - import the StrategySwitcher class directly
from core.strategies.strategy_switcher import StrategySwitcher

# Create global instance for use in routes
strategy_switcher = StrategySwitcher()

from flask import Blueprint, request, jsonify

# Create blueprint for strategy switcher routes
api_strategy_switcher = Blueprint('api_strategy_switcher', __name__)

@api_strategy_switcher.route('/switch-strategy', methods=['POST'])
def switch_strategy():
    """Switch strategy based on API request"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract strategy parameters from request
        symbol = data.get('symbol')
        strategy_id = data.get('strategy')
        
        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400
            
        # Use the strategy switcher to switch strategies
        result = strategy_switcher.evaluate_and_switch({symbol: data.get('data', {})})
        
        if result:
            return jsonify({
                'success': True,
                'message': 'Strategy switched successfully',
                'current_strategy': strategy_switcher.current_strategy,
                'score': result.get('score', 0)
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'No strategy switch performed'
            }), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_strategy_switcher.route('/strategy-status', methods=['GET'])
def strategy_status():
    """Get current strategy status"""
    try:
        status = {
            'current_strategy': strategy_switcher.current_strategy,
            'current_score': strategy_switcher.current_score,
            'last_switched': strategy_switcher.last_switch_time.isoformat() if strategy_switcher.last_switch_time else None,
            'switch_history': strategy_switcher.get_switch_history()
        }
        return jsonify(status), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Register the blueprint with the application
def register_routes(app):
    app.register_blueprint(api_strategy_switcher)