# core/routes/api_bots.py

import json
import logging
from flask import Blueprint, jsonify, request
import MetaTrader5 as mt5
from core.bots import controller
from core.db import queries
from core.utils.mt5 import get_rates_mt5
from core.utils.mt5 import TIMEFRAME_MAP
from core.strategies.strategy_map import STRATEGY_MAP, resolve_strategy_class
from core.bots.controller import health_check_bots, start_health_watchdog, stop_health_watchdog

api_bots = Blueprint('api_bots', __name__)
logger = logging.getLogger(__name__)

@api_bots.route('/api/strategies', methods=['GET'])
def get_strategies_route():
    try:
        strategies = []
        for key, strategy_class in STRATEGY_MAP.items():
            strategies.append({
                'id': key,
                'name': getattr(strategy_class, 'name', key.replace('_', ' ').title()),
                'description': getattr(strategy_class, 'description', 'No description available.')
            })
        return jsonify(strategies)
    except Exception as e:
        logger.error(f"Gagal memuat daftar strategi: {e}", exc_info=True)
        return jsonify({"error": "Gagal memuat daftar strategi"}), 500

@api_bots.route('/api/strategies/<strategy_id>/params', methods=['GET'])
def get_strategy_params_route(strategy_id):
    """Mengembalikan parameter yang bisa diatur untuk sebuah strategi."""
    strategy_class = resolve_strategy_class(strategy_id)
    if not strategy_class:
        return jsonify({"error": "Strategi tidak ditemukan"}), 404
    
    # Panggil metode class untuk mendapatkan parameter
    if hasattr(strategy_class, 'get_definable_params'):
        params = strategy_class.get_definable_params()
        
        # Normalize parameter format for frontend compatibility
        # Frontend expects 'label' but some strategies use 'display_name'
        normalized_params = []
        for param in params:
            normalized_param = param.copy()
            # If display_name exists but label doesn't, use display_name as label
            if 'display_name' in param and 'label' not in param:
                normalized_param['label'] = param['display_name']
            # If neither exists, create a label from the name
            elif 'label' not in param and 'display_name' not in param:
                normalized_param['label'] = param['name'].replace('_', ' ').title()
            normalized_params.append(normalized_param)
        
        return jsonify(normalized_params)
    
    return jsonify([]) # Kembalikan array kosong jika tidak ada parameter

@api_bots.route('/api/bots', methods=['GET'])
def get_bots_route():
    """Mengambil semua bot, termasuk AI prediction."""
    bots = queries.get_all_bots()
    
    # 获取活跃机器人的 AI 预测
    from core.bots.controller import active_bots
    
    for bot in bots:
        strategy_key = bot.get('strategy')
        strategy_class = resolve_strategy_class(strategy_key)
        bot['strategy_name'] = getattr(strategy_class, 'name', strategy_key) if strategy_class else strategy_key
        
        # 附加 AI 预测信息
        bot_id = bot['id']
        if bot_id in active_bots:
            bot_instance = active_bots[bot_id]
            if hasattr(bot_instance, 'last_ml_result') and bot_instance.last_ml_result:
                bot['ai_state'] = bot_instance.last_ml_result.get('state', -1)
                bot['ai_confidence'] = bot_instance.last_ml_result.get('confidence', 0.0)
                # 从 state_strategy_map 获取推荐策略
                from core.ai.state_strategy_map import STATE_STRATEGY_MAP
                ai_state = bot['ai_state']
                if ai_state in STATE_STRATEGY_MAP:
                    bot['ai_suggested_strategy'] = STATE_STRATEGY_MAP[ai_state]['strategy']
                else:
                    bot['ai_suggested_strategy'] = None
            else:
                bot['ai_state'] = -1
                bot['ai_confidence'] = 0.0
                bot['ai_suggested_strategy'] = None
        else:
            bot['ai_state'] = -1
            bot['ai_confidence'] = 0.0
            bot['ai_suggested_strategy'] = None
            
    return jsonify(bots)

@api_bots.route('/api/bots/<int:bot_id>', methods=['GET'])
def get_single_bot_route(bot_id):
    """Mengambil detail satu bot."""
    bot = queries.get_bot_by_id(bot_id)
    if bot and bot.get('strategy_params'):
        # Ubah string JSON menjadi objek untuk frontend
        bot['strategy_params'] = json.loads(bot['strategy_params'])
    # Convert enable_strategy_switching to integer for frontend
    if bot and 'enable_strategy_switching' in bot:
        bot['enable_strategy_switching'] = int(bot['enable_strategy_switching'])
    return jsonify(bot) if bot else (jsonify({"error": "Bot tidak ditemukan"}), 404)

@api_bots.route('/api/bots', methods=['POST'])
def add_bot_route():
    """Membuat bot baru."""
    data = request.get_json()
    params_json = json.dumps(data.get('params', {}))
    
    # Get strategy switching setting
    enable_strategy_switching = int(data.get('enable_strategy_switching', False))

    new_bot_id = queries.add_bot(
        name=data.get('name'), market=data.get('market'), lot_size=data.get('risk_percent'),
        sl_pips=data.get('sl_atr_multiplier'), tp_pips=data.get('tp_atr_multiplier'), timeframe=data.get('timeframe'),
        interval=data.get('check_interval_seconds'), strategy=data.get('strategy'),
        strategy_params=params_json, enable_strategy_switching=enable_strategy_switching
    )
    if new_bot_id:
        controller.add_new_bot_to_controller(new_bot_id)
        return jsonify({"message": "Bot berhasil dibuat", "bot_id": new_bot_id}), 201
    return jsonify({"error": "Gagal menyimpan bot"}), 500

@api_bots.route('/api/bots/<int:bot_id>', methods=['PUT'])
def update_bot_route(bot_id):
    """Memperbarui pengaturan bot."""
    bot_data = request.get_json()
    
    bot_instance = controller.get_bot_instance_by_id(bot_id)
    bot_was_running = bot_instance and bot_instance.status == 'Aktif'
    
    # Get strategy switching setting
    enable_strategy_switching = int(bot_data.get('enable_strategy_switching', False))

    success, result = controller.perbarui_bot(bot_id, bot_data)
    
    # Update the database with the strategy switching setting
    if success:
        queries.update_bot(
            bot_id=bot_id,
            name=bot_data.get('name'),
            market=bot_data.get('market'),
            lot_size=bot_data.get('risk_percent'),
            sl_pips=bot_data.get('sl_atr_multiplier'),
            tp_pips=bot_data.get('tp_atr_multiplier'),
            timeframe=bot_data.get('timeframe'),
            interval=bot_data.get('check_interval_seconds'),
            strategy=bot_data.get('strategy'),
            strategy_params=json.dumps(bot_data.get('params', {})),
            enable_strategy_switching=enable_strategy_switching
        )
        
        if bot_was_running:
            controller.mulai_bot(bot_id)
        return jsonify({"message": "Bot berhasil diperbarui."}), 200
    
    return jsonify({"error": result or "Gagal memperbarui bot"}), 500

@api_bots.route('/api/bots/<int:bot_id>', methods=['DELETE'])
def delete_bot_route(bot_id):
    """Menghapus bot."""
    if controller.hapus_bot(bot_id):
        return jsonify({"message": "Bot berhasil dihapus."}), 200
    else:
        return jsonify({"error": "Gagal menghapus bot dari database"}), 500

@api_bots.route('/api/bots/<int:bot_id>/start', methods=['POST'])
def start_bot_route(bot_id):
    """Memulai bot."""
    success, message = controller.mulai_bot(bot_id)
    return jsonify({'message': message}) if success else (jsonify({'error': message}), 500)

@api_bots.route('/api/bots/<int:bot_id>/stop', methods=['POST'])
def stop_bot_route(bot_id):
    """Menghentikan bot."""
    success, message = controller.hentikan_bot(bot_id)
    return jsonify({'message': message}) if success else (jsonify({'error': message}), 500)

@api_bots.route('/api/bots/start_all', methods=['POST'])
def start_all_bots_route():
    """Memulai semua bot yang dijeda."""
    success, message = controller.mulai_semua_bot()
    return jsonify({'message': message}) if success else (jsonify({'error': message}), 400)

@api_bots.route('/api/bots/stop_all', methods=['POST'])
def stop_all_bots_route():
    """Menghentikan semua bot yang aktif."""
    success, message = controller.hentikan_semua_bot()
    return jsonify({'message': message}) if success else (jsonify({'error': message}), 400)

@api_bots.route('/api/bots/<int:bot_id>/analysis', methods=['GET'])
def get_analysis_route(bot_id):
    """Mendapatkan data analisis terakhir."""
    data = controller.get_bot_analysis_data(bot_id)
    return jsonify(data if data else {"signal": "Data belum tersedia"})

@api_bots.route('/api/bots/<int:bot_id>/history', methods=['GET'])
def get_bot_history_route(bot_id):
    """Mengembalikan riwayat aktivitas untuk bot."""
    history = queries.get_history_by_bot_id(bot_id)
    return jsonify(history)

@api_bots.route('/api/rsi_data', methods=['GET'])
def get_rsi_data_route():
    """Menyediakan data RSI untuk grafik di dashboard."""
    symbol = request.args.get('symbol', 'XAUUSDm', type=str)
    timeframe_str = request.args.get('timeframe', 'H1', type=str)
    
    timeframe = TIMEFRAME_MAP.get(timeframe_str.upper(), mt5.TIMEFRAME_H1)
    
    df = get_rates_mt5(symbol, timeframe, 100)
    
    if df is None or df.empty:
        return jsonify({"error": f"Tidak dapat mengambil data untuk {symbol}"}), 404
        
    df.ta.rsi(length=14, append=True)
    df.dropna(inplace=True)
    
    last_50_rows = df.tail(50)

    chart_data = {
        'timestamps': [ts.strftime('%H:%M') for ts in last_50_rows.index],
        'rsi_values': list(last_50_rows.iloc[:, -1])
    }
    return jsonify(chart_data)


@api_bots.route('/bots/health', methods=['GET', 'POST'])
def bots_health():
    """觸發 bot 健康檢查（watchdog 一次性掃描 + 回傳狀態）"""
    result = health_check_bots()
    return jsonify({'success': True, 'data': result})


@api_bots.route('/bots/watchdog/start', methods=['POST'])
def watchdog_start():
    data = request.get_json(silent=True) or {}
    interval = data.get('interval', 60)
    start_health_watchdog(interval)
    return jsonify({'success': True, 'message': f'Watchdog started every {interval}s'})


@api_bots.route('/bots/watchdog/stop', methods=['POST'])
def watchdog_stop():
    stop_health_watchdog()
    return jsonify({'success': True, 'message': 'Watchdog stopped'})
