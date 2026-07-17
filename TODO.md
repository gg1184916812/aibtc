# TODO - 修復 AI 回測 stop_out_ratio 錯誤

- [ ] Step 1: 確認 AIBacktester.__init__ 不接受 stop_out_ratio（已知錯誤來源）。
- [ ] Step 2: 修復呼叫端：移除在 AIBacktester 建構子中傳入 stop_out_ratio 的用法，或改為在建構後設定屬性。
- [ ] Step 3: 在回測器內補上 stop_out_ratio/stopped_out/stop_out 相關欄位與 stop 邏輯（若目前缺失）。
- [ ] Step 4: 更新 API 回測 run(df) 的參數處理，確保不會再丟出 unexpected keyword argument。
- [ ] Step 5: 執行一次回測測試（XAUUSDm_M5_data.csv + XAUUSDm_M5_online.pkl），確認可跑完並輸出結果。

