#!/usr/bin/env python3
"""
训练价格目标预测模型
用法: python scripts/train_price_target.py --symbol XAUUSDm --timeframe M5
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ai.price_target_predictor import PriceTargetPredictor

def find_data_file(symbol: str, timeframe: str) -> str:
    """查找数据文件"""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backtest_data')
    
    # 尝试多种文件名格式
    candidates = [
        os.path.join(data_dir, f"{symbol}_{timeframe}_data.csv"),
        os.path.join(data_dir, f"{symbol}_{timeframe}.csv"),
    ]
    
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    
    # 尝试匹配任意以 symbol 开头的文件
    for f in os.listdir(data_dir):
        if f.startswith(symbol) and timeframe in f and f.endswith('.csv'):
            return os.path.join(data_dir, f)
    
    return None

def main():
    parser = argparse.ArgumentParser(description='训练价格目标预测模型')
    parser.add_argument('--symbol', default='XAUUSDm', help='交易品种')
    parser.add_argument('--timeframe', default='M5', help='时间周期')
    parser.add_argument('--forward_bars', type=int, default=20, help='预测未来 K 线数量')
    parser.add_argument('--data_file', help='数据文件路径（可选）')
    args = parser.parse_args()
    
    print("="*70)
    print("🎯 价格目标预测模型训练")
    print("="*70)
    print(f"📊 品种: {args.symbol}")
    print(f"⏱️ 周期: {args.timeframe}")
    print(f"📈 预测窗口: {args.forward_bars} 根K线")
    print("="*70)
    
    # 查找数据文件
    if args.data_file:
        data_file = args.data_file
    else:
        data_file = find_data_file(args.symbol, args.timeframe)
    
    if not data_file:
        print(f"❌ 未找到数据文件: {args.symbol} {args.timeframe}")
        print("💡 请先运行数据下载服务")
        sys.exit(1)
    
    print(f"📂 数据文件: {data_file}")
    
    # 加载数据
    df = pd.read_csv(data_file, parse_dates=['time'])
    print(f"📊 数据量: {len(df)} 根 K 线")
    
    # 训练模型
    predictor = PriceTargetPredictor()
    predictor.train(df, forward_bars=args.forward_bars)
    
    # 保存模型
    model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ai_models')
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, f"{args.symbol}_{args.timeframe}_price_target.pkl")
    predictor.save(model_path)
    
    print("\n" + "="*70)
    print("✅ 价格目标模型训练完成!")
    print(f"📁 模型保存至: {model_path}")
    print("="*70)


if __name__ == "__main__":
    main()