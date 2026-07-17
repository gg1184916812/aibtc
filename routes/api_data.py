# core/routes/api_data.py
"""
数据下载 API 端点
提供自动数据下载服务的控制接口
"""

import os
import json
import time
import logging
from flask import Blueprint, request, jsonify, Response, stream_with_context
from datetime import datetime

from core.services.data_download_service import get_download_service

api_data = Blueprint('api_data', __name__, url_prefix='/api/data')
logger = logging.getLogger(__name__)


@api_data.route('/download/status', methods=['GET'])
def get_status():
    """获取下载服务状态"""
    service = get_download_service()
    return jsonify({
        'success': True,
        'data': service.get_status()
    })


@api_data.route('/download/start', methods=['POST'])
def start_service():
    """启动下载服务"""
    service = get_download_service()
    success, msg = service.start()
    return jsonify({'success': success, 'message': msg})


@api_data.route('/download/stop', methods=['POST'])
def stop_service():
    """停止下载服务"""
    service = get_download_service()
    success, msg = service.stop()
    return jsonify({'success': success, 'message': msg})


@api_data.route('/download/manual', methods=['POST'])
def manual_download():
    """手动下载指定品种和周期"""
    data = request.get_json()
    symbol = data.get('symbol', 'XAUUSDm')
    timeframe = data.get('timeframe', 'H1')
    
    service = get_download_service()
    service.manual_download(symbol, timeframe)
    
    return jsonify({'success': True, 'message': f'已触发下载: {symbol} {timeframe}'})


@api_data.route('/files', methods=['GET'])
def get_files():
    """获取所有已下载的数据文件"""
    import pandas as pd
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'backtest_data')
    
    files = []
    if os.path.exists(data_dir):
        for f in os.listdir(data_dir):
            if f.endswith('.csv'):
                file_path = os.path.join(data_dir, f)
                stat = os.stat(file_path)
                try:
                    df = pd.read_csv(file_path)
                    rows = len(df)
                except:
                    rows = 0
                
                parts = f.replace('_data.csv', '').split('_')
                symbol = parts[0] if len(parts) > 0 else 'Unknown'
                timeframe = parts[1] if len(parts) > 1 else 'Unknown'
                
                date_range = ''
                try:
                    df_time = pd.read_csv(file_path, parse_dates=['time'])
                    if not df_time.empty:
                        date_range = f"{df_time['time'].min().strftime('%Y-%m-%d')} ~ {df_time['time'].max().strftime('%Y-%m-%d')}"
                except:
                    pass
                
                files.append({
                    'filename': f,
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'size': stat.st_size,
                    'rows': rows,
                    'date_range': date_range,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
    
    return jsonify({'success': True, 'data': sorted(files, key=lambda x: x['modified'], reverse=True)})


@api_data.route('/download/logs/stream')
def stream_logs():
    """SSE 推送下载日志"""
    service = get_download_service()
    
    def generate():
        last_count = 0
        # 立即发送一条连接成功消息
        yield f"data: {json.dumps({'timestamp': datetime.now().strftime('%H:%M:%S'), 'message': '📡 日志流已连接', 'level': 'info'})}\n\n"
        
        while True:
            try:
                logs = service.logs
                if len(logs) > last_count:
                    for log in logs[last_count:]:
                        yield f"data: {json.dumps(log)}\n\n"
                    last_count = len(logs)
                time.sleep(1)
            except Exception as e:
                yield f"data: {json.dumps({'timestamp': datetime.now().strftime('%H:%M:%S'), 'message': f'日志流错误: {e}', 'level': 'error'})}\n\n"
                time.sleep(5)
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')