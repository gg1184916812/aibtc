# run.py
import os
import sys
import atexit
import logging
import MetaTrader5 as mt5
from flask import jsonify
from core import create_app
from core.utils.mt5 import initialize_mt5
from core.bots.controller import shutdown_all_bots, ambil_semua_bot, start_health_watchdog, stop_health_watchdog
from core.ai.online_learner import start_all_schedulers, stop_all_schedulers
from dotenv import load_dotenv

load_dotenv()

# 如果环境变量中指定了 DB_NAME，则使用，否则默认 bots.db
DB_NAME = os.getenv('DB_NAME', 'bots.db')
os.environ['DB_NAME'] = DB_NAME  # 传递给 core

# 端口也从环境变量读取，默认 5001
PORT = int(os.getenv('FLASK_PORT', 5001))

# 在线学习：預設不啟動，只有設定 ENABLE_ONLINE_LEARNING=1 才會在 run 時自動訓練
ENABLE_ONLINE_LEARNING = os.getenv('ENABLE_ONLINE_LEARNING', '0').lower() in ('1', 'true', 'yes')

logging.getLogger('werkzeug').setLevel(logging.WARNING)

def shutdown_app():
    logging.info("Memulai proses shutdown aplikasi...")
    shutdown_all_bots()
    mt5.shutdown()
    logging.info("Koneksi MetaTrader 5 ditutup. Aplikasi berhenti.")

app = create_app()

@app.route('/api/health')
def health_check():
    mt5_status = "MT5 connected" if mt5.terminal_info() else "MT5 not connected"
    return jsonify({"status": "ok", "message": "Server is running", "mt5": mt5_status})


try:
    account_str = os.getenv('MT5_LOGIN')
    password = os.getenv('MT5_PASSWORD')
    server = os.getenv('MT5_SERVER', 'MetaQuotes-Demo')
    if not account_str or not password:
        logging.error("Error: MT5_LOGIN dan MT5_PASSWORD harus diisi di file .env")
        sys.exit(1)
    account = int(account_str)
    if initialize_mt5(account, password, server):
        logging.info("Koneksi MT5 berhasil diinisialisasi dari run.py.")
        ambil_semua_bot()
        start_health_watchdog(60)  # 每 60 秒巡檢一次
        if ENABLE_ONLINE_LEARNING:
            start_all_schedulers()     # 啟動在線學習排程
            atexit.register(stop_all_schedulers)
        else:
            logging.info("ENABLE_ONLINE_LEARNING=0，啟動時不會自動訓練模型。")
        atexit.register(shutdown_app)
        atexit.register(stop_health_watchdog)
    else:
        logging.error("Error: Gagal terhubung ke MT5.")
        sys.exit(1)
except Exception as e:
    logging.critical(f"GAGAL total saat inisialisasi MT5: {e}", exc_info=True)

app.run(
    debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
    host=os.getenv('FLASK_HOST', '127.0.0.1'),
    port=PORT,
    use_reloader=False
)