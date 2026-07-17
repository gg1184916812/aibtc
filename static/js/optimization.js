// static/js/optimization.js
document.addEventListener('DOMContentLoaded', () => {
    const strategySelect = document.getElementById('strategy-select');
    const strategyOptParams = document.getElementById('strategy-opt-params');
    const form = document.getElementById('optimize-form');
    const runBtn = document.getElementById('run-optimize-btn');
    const cancelBtn = document.getElementById('cancel-optimize-btn');
    const resultsContainer = document.getElementById('results-container');
    const optimizeSummary = document.getElementById('optimize-summary');
    const applyToBacktest = document.getElementById('apply-to-backtest');
    const addBotBtn = document.getElementById('add-bot-from-optimize');
    const optimizerSelect = document.getElementById('optimizer-select');
    const wfoCheckbox = document.getElementById('wfo-enabled');
    const liveBest = document.getElementById('live-best');
    const liveBestContent = document.getElementById('live-best-content');
    const progressArea = document.getElementById('progress-area');
    const progressPhase = document.getElementById('progress-phase');
    const progressText = document.getElementById('progress-text');
    const progressBar = document.getElementById('progress-bar');
    const liveLog = document.getElementById('live-log');
    const wfoSummary = document.getElementById('wfo-summary');
    const paretoSummary = document.getElementById('pareto-summary');
    const allResultsTable = document.getElementById('all-results-table');
    let optimizeChart = null;
    let currentTaskId = null;
    let eventSource = null;
    let bestParamsCache = null;
    let bestResultCache = null;
    let allResultsCache = [];
    let logsCache = [];

    const BACKTEST_KEY = 'quantumBotX_backtest_defaults';
    const BOT_KEY = 'quantumBotX_bot_defaults';

    setDefaultDates();

    function setDefaultDates() {
        const today = new Date();
        const threeMonthsAgo = new Date(today);
        threeMonthsAgo.setMonth(threeMonthsAgo.getMonth() - 3);
        document.getElementById('date-from').value = threeMonthsAgo.toISOString().split('T')[0];
        document.getElementById('date-to').value = today.toISOString().split('T')[0];
    }

    async function loadStrategies() {
        try {
            const response = await fetch('/api/strategies');
            const strategies = await response.json();
            strategySelect.innerHTML = '<option value="" disabled selected>請選擇策略</option>';
            strategies.forEach(s => {
                const opt = document.createElement('option');
                opt.value = s.id;
                opt.textContent = s.name;
                strategySelect.appendChild(opt);
            });
        } catch (err) {
            console.error('Failed to load strategies:', err);
        }
    }

    strategySelect.addEventListener('change', async () => {
        const strategyId = strategySelect.value;
        strategyOptParams.innerHTML = '<p class="text-sm text-gray-500">載入參數中...</p>';
        if (!strategyId) { strategyOptParams.innerHTML = ''; return; }

        try {
            const res = await fetch(`/api/strategies/${strategyId}/params`);
            const params = await res.json();
            strategyOptParams.innerHTML = '<h4 class="text-sm font-semibold text-gray-700 mb-2">策略參數</h4>';

            if (params.length > 0) {
                params.forEach(param => {
                    const def = param.default || 10;
                    const mn = Math.max(1, Math.floor(def * 0.3));
                    const mx = Math.ceil(def * 2.0);
                    const st = Math.max(1, Math.round(def * 0.3));
                    strategyOptParams.innerHTML += `
                        <div class="border-b pb-2 mb-2">
                            <label class="block text-xs font-medium text-gray-600 mb-1">${param.label}</label>
                            <div class="grid grid-cols-3 gap-2">
                                <div>
                                    <span class="text-xs text-gray-400">最小</span>
                                    <input type="number" name="opt_${param.name}_min" value="${mn}" step="any" class="opt-param mt-1 block w-full rounded-md border-gray-300 text-sm">
                                </div>
                                <div>
                                    <span class="text-xs text-gray-400">最大</span>
                                    <input type="number" name="opt_${param.name}_max" value="${mx}" step="any" class="opt-param mt-1 block w-full rounded-md border-gray-300 text-sm">
                                </div>
                                <div>
                                    <span class="text-xs text-gray-400">步長</span>
                                    <input type="number" name="opt_${param.name}_step" value="${st}" step="any" class="opt-param mt-1 block w-full rounded-md border-gray-300 text-sm">
                                </div>
                            </div>
                        </div>`;
                });
            } else {
                strategyOptParams.innerHTML += '<p class="text-sm text-gray-500">此策略無自定義參數</p>';
            }
        } catch (e) {
            console.error(e);
            strategyOptParams.innerHTML = '<p class="text-sm text-red-500">載入參數失敗</p>';
        }
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const symbol = document.getElementById('symbol-select').value;
        const timeframe = document.getElementById('timeframe-select').value;
        const dateFrom = document.getElementById('date-from').value;
        const dateTo = document.getElementById('date-to').value;
        const strategy = strategySelect.value;

        if (!strategy) { alert('請選擇策略'); return; }
        if (!dateFrom || !dateTo) { alert('請選擇日期範圍'); return; }
        if (dateFrom >= dateTo) { alert('開始日期必須早於結束日期'); return; }

        const optimizationParams = {};
        ['risk_percent', 'sl_atr', 'tp_atr'].forEach(k => {
            optimizationParams[k] = {
                min: parseFloat(form.elements[`opt_${k}_min`].value) || 1,
                max: parseFloat(form.elements[`opt_${k}_max`].value) || 1,
                step: parseFloat(form.elements[`opt_${k}_step`].value) || 1
            };
        });
        document.querySelectorAll('#strategy-opt-params input[name$="_min"]').forEach(el => {
            const base = el.name.replace('opt_', '').replace('_min', '');
            const mn = parseFloat(el.value) || 1;
            const mx = parseFloat(form.elements[`opt_${base}_max`]?.value) || 1;
            const st = parseFloat(form.elements[`opt_${base}_step`]?.value) || 1;
            optimizationParams[base] = { min: mn, max: mx, step: st };
        });

        const payload = { symbol, timeframe, date_from: dateFrom, date_to: dateTo, strategy, optimization_params: optimizationParams,
            initial_capital: parseFloat(document.getElementById('initial_capital').value) || 100,
            optimizer: optimizerSelect.value,
            wfo_enabled: wfoCheckbox.checked };

        runBtn.disabled = true;
        runBtn.textContent = '啟動中...';
        cancelBtn.classList.remove('hidden');
        resultsContainer.classList.remove('hidden');
        progressArea.classList.remove('hidden');
        liveLog.innerHTML = '<div class="text-gray-400 text-sm py-2 px-1">⌛ 正在連線並下載 MT5 數據，請稍候...</div>';

        try {
            const resp = await fetch('/api/backtest/optimize/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await resp.json();
            if (!resp.ok) { alert(`錯誤: ${data.error}`); resetUI(); return; }

            currentTaskId = data.task_id;
            runBtn.classList.add('hidden');
            cancelBtn.classList.remove('hidden');
            startSSE(currentTaskId);
        } catch (err) {
            console.error(err);
            alert('連接伺服器失敗');
            resetUI();
        }
    });

    function startSSE(taskId) {
        eventSource = new EventSource(`/api/backtest/optimize/stream/${taskId}`);
        allResultsCache = [];
        logsCache = [];

        eventSource.onmessage = (event) => {
            const payload = JSON.parse(event.data);
            if (payload.error) { console.error(payload.error); return; }

            if (payload.total > 0 || payload.total_phases > 1) {
                const optName = {
                    'grid': '網格', 'optuna_tpe': 'TPE', 'optuna_multiobj': '多目標', 'de': 'DE'
                }[payload.optimizer] || '';

                if (payload.wfo_enabled && payload.total_phases > 1) {
                    progressPhase.textContent = `WFO 窗口 ${payload.phase}/${payload.total_phases}`;
                    const perWindow = Math.min(payload.progress / Math.max(payload.total, 1), 1);
                    const overall = ((payload.phase - 1) + perWindow) / payload.total_phases;
                    progressText.textContent = `窗${payload.phase}: ${payload.progress}/${payload.total}　總進度 ${(overall*100).toFixed(0)}%`;
                    progressBar.style.width = `${(overall * 100).toFixed(0)}%`;
                } else if (payload.total_phases > 1 && !payload.wfo_enabled) {
                    const perPhase = Math.min(payload.progress / Math.max(payload.total, 1), 1);
                    const overall = ((payload.phase - 1) + perPhase) / payload.total_phases;
                    progressPhase.textContent = `${optName} 階段 ${payload.phase}/${payload.total_phases}`;
                    progressText.textContent = `階段${payload.phase}: ${payload.progress}/${payload.total}　總進度 ${(overall*100).toFixed(0)}%`;
                    progressBar.style.width = `${(overall * 100).toFixed(0)}%`;
                } else {
                    progressPhase.textContent = `${optName} 優化中`;
                    progressText.textContent = `${payload.progress} / ${payload.total}`;
                    progressBar.style.width = `${payload.total > 0 ? (payload.progress / payload.total) * 100 : 0}%`;
                }
            }

            // Live best
            if (payload.best_result_summary) {
                liveBest.classList.remove('hidden');
                const s = payload.best_result_summary;
                let paramsStr = '';
                if (payload.best_params) {
                    paramsStr = Object.entries(payload.best_params)
                        .map(([k, v]) => `${k}=${typeof v === 'number' ? v.toFixed(2) : v}`).join(', ');
                }
                liveBestContent.innerHTML = `
                    <p>淨利: <span class="font-bold ${s.total_profit_usd >= 0 ? 'text-green-700' : 'text-red-700'}">$${s.total_profit_usd.toFixed(2)}</span>
                    勝率: <span class="font-bold">${s.win_rate_percent.toFixed(0)}%</span>
                    回撤: <span class="font-bold text-red-600">${s.max_drawdown_percent.toFixed(2)}%</span>
                    交易: <span class="font-bold">${s.total_trades}</span></p>
                    <p class="text-xs text-gray-500 mt-1">${paramsStr}</p>`;
                bestParamsCache = payload.best_params;
                bestResultCache = payload.best_result_summary;
            }

            // Logs - real-time display
            if (payload.logs && payload.logs.length > 0) {
                payload.logs.forEach(log => {
                    logsCache.push(log);
                    const div = document.createElement('div');
                    let phaseLabel = '';
                    if (payload.wfo_enabled && log.phase <= payload.total_phases) {
                        phaseLabel = `<span class="text-xs px-1 py-0.5 mr-1 rounded bg-orange-100 text-orange-700">W${log.phase}</span>`;
                    } else if (payload.total_phases > 1 && !payload.wfo_enabled) {
                        phaseLabel = `<span class="text-xs px-1 py-0.5 mr-1 rounded ${log.phase === 1 ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'}">P${log.phase}</span>`;
                    } else if (payload.optimizer) {
                        const initial = {'grid':'G','optuna_tpe':'T','optuna_multiobj':'M','de':'D'}[payload.optimizer] || '';
                        phaseLabel = `<span class="text-xs px-1 py-0.5 mr-1 rounded bg-gray-100 text-gray-600">${initial}</span>`;
                    }
                    const isProgress = /已完成.*組|第.*次/.test(log.msg);
                    div.className = 'py-1 text-sm ' +
                        (log.is_best
                            ? 'bg-green-100 font-bold text-green-800 px-1.5 rounded my-0.5'
                            : isProgress
                                ? 'text-gray-400 px-1'
                                : 'text-gray-700 px-1');
                    div.innerHTML = `<span class="text-xs text-gray-400 mr-1.5">${log.time}</span>${phaseLabel}${log.msg}`;
                    if (log.is_best) {
                        liveLog.prepend(div);
                    } else {
                        liveLog.appendChild(div);
                    }
                });
                liveLog.scrollTop = liveLog.scrollHeight;
            }

            if (payload.done) {
                onOptimizationDone();
            }
        };

        eventSource.onerror = () => {
            eventSource.close();
            onOptimizationDone();
        };
    }

    async function onOptimizationDone() {
        if (eventSource) { eventSource.close(); eventSource = null; }
        resetUI();

        if (currentTaskId) {
            try {
                const resp = await fetch(`/api/backtest/optimize/result/${currentTaskId}`);
                const result = await resp.json();
                if (resp.ok && result.best_result) {
                    bestParamsCache = result.best_params;
                    bestResultCache = result.best_result_summary;
                    allResultsCache = result.all_results || [];
                    displayFinalResults(result);
                }
            } catch (e) { console.error(e); }
        }
    }

    cancelBtn.addEventListener('click', async () => {
        if (!currentTaskId) return;
        cancelBtn.disabled = true;
        cancelBtn.textContent = '取消中...';
        try {
            await fetch(`/api/backtest/optimize/cancel/${currentTaskId}`, { method: 'POST' });
        } catch (e) { console.error(e); }
    });

    function resetUI() {
        runBtn.classList.remove('hidden');
        runBtn.disabled = false;
        runBtn.textContent = '開始優化';
        cancelBtn.classList.add('hidden');
        cancelBtn.disabled = false;
        cancelBtn.textContent = '取消';
        if (eventSource) { eventSource.close(); eventSource = null; }
    }

    function displayFinalResults(result) {
        const best = result.best_result || {};
        const netProfit = best.net_profit_after_costs ?? best.total_profit_usd ?? 0;

        optimizeSummary.innerHTML = `
            <div class="p-4 bg-gray-50 rounded-lg">
                <p class="text-sm text-gray-500">總測試組合</p>
                <p class="text-2xl font-bold text-blue-600">${result.total_combinations || 0}</p>
            </div>
            <div class="p-4 bg-gray-50 rounded-lg">
                <p class="text-sm text-gray-500">最佳淨利潤</p>
                <p class="text-2xl font-bold ${netProfit >= 0 ? 'text-green-600' : 'text-red-600'}">${netProfit.toFixed(2)} $</p>
            </div>
            <div class="p-4 bg-gray-50 rounded-lg">
                <p class="text-sm text-gray-500">勝率</p>
                <p class="text-2xl font-bold text-blue-600">${(best.win_rate_percent || 0).toFixed(1)}%</p>
            </div>
            <div class="p-4 bg-gray-50 rounded-lg">
                <p class="text-sm text-gray-500">最大回撤</p>
                <p class="text-2xl font-bold text-red-600">${(best.max_drawdown_percent || 0).toFixed(2)}%</p>
            </div>
            <div class="p-4 bg-gray-50 rounded-lg">
                <p class="text-sm text-gray-500">總交易</p>
                <p class="text-2xl font-bold">${best.total_trades || 0}</p>
            </div>
        `;

        if (result.wfo_windows && result.wfo_windows.length > 0) {
            let wfoHtml = '<h4 class="text-sm font-semibold text-orange-800 mb-2">WFO 窗口驗證摘要</h4>';
            wfoHtml += '<table class="w-full text-xs bg-white rounded border"><thead><tr class="bg-orange-100">';
            wfoHtml += '<th class="p-1 border">窗口</th><th class="p-1 border">訓練淨利</th><th class="p-1 border">測試淨利</th><th class="p-1 border">測試回撤</th></tr></thead><tbody>';
            result.wfo_windows.forEach(w => {
                wfoHtml += `<tr>
                    <td class="p-1 border text-center font-bold">#${w.window + 1}</td>
                    <td class="p-1 border text-right ${w.train_profit >= 0 ? 'text-green-600' : 'text-red-600'}">$${w.train_profit.toFixed(2)}</td>
                    <td class="p-1 border text-right ${w.test_profit >= 0 ? 'text-green-600' : 'text-red-600'}">$${w.test_profit.toFixed(2)}</td>
                    <td class="p-1 border text-center">${w.test_drawdown.toFixed(2)}%</td>
                </tr>`;
            });
            wfoHtml += '</tbody></table>';
            wfoSummary.innerHTML = wfoHtml;
            wfoSummary.classList.remove('hidden');
        } else {
            wfoSummary.classList.add('hidden');
        }

        if (result.pareto_front && result.pareto_front.length > 0) {
            let paretoHtml = `<h4 class="text-sm font-semibold text-purple-800 mb-2">Pareto 前沿（${result.pareto_front.length} 個最優解）</h4>`;
            paretoHtml += '<table class="w-full text-xs bg-white rounded border"><thead><tr class="bg-purple-100">';
            paretoHtml += '<th class="p-1 border">#</th><th class="p-1 border">淨利</th><th class="p-1 border">回撤</th><th class="p-1 border">參數</th></tr></thead><tbody>';
            result.pareto_front.forEach((p, i) => {
                const paramsStr = Object.entries(p.params).map(([k, v]) => `${k}=${v.toFixed(2)}`).join(', ');
                paretoHtml += `<tr>
                    <td class="p-1 border text-center">${i + 1}</td>
                    <td class="p-1 border text-right ${p.profit >= 0 ? 'text-green-600' : 'text-red-600'}">$${p.profit.toFixed(2)}</td>
                    <td class="p-1 border text-right">${p.drawdown.toFixed(2)}%</td>
                    <td class="p-1 border text-xs">${paramsStr}</td>
                </tr>`;
            });
            paretoHtml += '</tbody></table>';
            paretoSummary.innerHTML = paretoHtml;
            paretoSummary.classList.remove('hidden');
        } else {
            paretoSummary.classList.add('hidden');
        }

        displayChart(result.all_results || []);

        if (result.all_results && result.all_results.length > 0) {
            const sorted = [...result.all_results].sort((a, b) => (b.total_profit_usd || 0) - (a.total_profit_usd || 0));
            let html = '<h4 class="text-lg font-semibold mt-4 mb-2">所有結果 (按淨利潤排序)</h4>';
            html += '<table class="w-full text-xs border"><thead><tr class="bg-gray-100">';
            const firstParams = sorted[0].params || {};
            Object.keys(firstParams).forEach(k => { html += `<th class="p-1 border">${k}</th>`; });
            html += '<th class="p-1 border">淨利潤</th><th class="p-1 border">勝率</th><th class="p-1 border">回撤</th><th class="p-1 border">交易</th></tr></thead><tbody>';
            const bestKey = JSON.stringify(result.best_params || {});
            sorted.slice(0, 100).forEach(r => {
                const thisKey = JSON.stringify(r.params || {});
                const isBest = bestKey === thisKey;
                html += `<tr class="${isBest ? 'bg-green-50 font-bold' : ''}">`;
                Object.values(r.params || {}).forEach(v => { html += `<td class="p-1 border text-center">${typeof v === 'number' ? v.toFixed(2) : v}</td>`; });
                html += `<td class="p-1 border text-right ${(r.total_profit_usd || 0) >= 0 ? 'text-green-600' : 'text-red-600'}">${(r.total_profit_usd || 0).toFixed(2)}</td>`;
                html += `<td class="p-1 border text-center">${(r.win_rate_percent || 0).toFixed(0)}%</td>`;
                html += `<td class="p-1 border text-center">${(r.max_drawdown_percent || 0).toFixed(1)}%</td>`;
                html += `<td class="p-1 border text-center">${r.total_trades || 0}</td>`;
                html += '</tr>';
            });
            html += '</tbody></table>';
            allResultsTable.innerHTML = html;
        }
    }

    function displayChart(allResults) {
        const ctx = document.getElementById('optimize-chart').getContext('2d');
        if (optimizeChart) optimizeChart.destroy();
        const sorted = [...allResults].sort((a, b) => (b.total_profit_usd || 0) - (a.total_profit_usd || 0));
        const topN = sorted.slice(0, 50);
        optimizeChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: topN.map((_, i) => `#${i + 1}`),
                datasets: [{
                    label: '淨利潤 ($)',
                    data: topN.map(r => r.total_profit_usd || 0),
                    backgroundColor: topN.map(r => (r.total_profit_usd || 0) >= 0 ? 'rgba(34,197,94,0.6)' : 'rgba(239,68,68,0.6)'),
                    borderColor: topN.map(r => (r.total_profit_usd || 0) >= 0 ? 'rgb(34,197,94)' : 'rgb(239,68,68)'),
                    borderWidth: 1,
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false }, title: { display: true, text: '前 50 組淨利潤排名' } },
                scales: { y: { beginAtZero: false } }
            }
        });
    }

    applyToBacktest.addEventListener('click', () => {
        if (!bestParamsCache) { alert('請先執行優化'); return; }
        const symbol = document.getElementById('symbol-select').value;
        const timeframe = document.getElementById('timeframe-select').value;
        const strategy = strategySelect.value;
        const defaults = {
            symbol, timeframe, strategy,
            initial_capital: parseFloat(document.getElementById('initial_capital').value) || 100,
            risk_percent: bestParamsCache.risk_percent || 1.0,
            sl_atr_multiplier: bestParamsCache.sl_atr || 2.0,
            tp_atr_multiplier: bestParamsCache.tp_atr || 4.0,
            params: {}
        };
        Object.keys(bestParamsCache).forEach(k => {
            if (!['risk_percent', 'sl_atr', 'tp_atr'].includes(k)) {
                defaults.params[k] = bestParamsCache[k];
            }
        });
        localStorage.setItem(BACKTEST_KEY, JSON.stringify(defaults));
        localStorage.setItem(BOT_KEY, JSON.stringify({
            symbol, strategy, timeframe,
            risk_percent: defaults.risk_percent,
            sl_atr_multiplier: defaults.sl_atr_multiplier,
            tp_atr_multiplier: defaults.tp_atr_multiplier,
            params: defaults.params,
            check_interval_seconds: 1,
            enable_strategy_switching: true
        }));
        if (typeof Toastify !== 'undefined') {
            Toastify({ text: '已填入回測預設值', duration: 3000, gravity: 'top', position: 'right', style: { background: '#16a34a' } }).showToast();
        } else {
            alert('已填入回測預設值');
        }
        window.open('/backtesting', '_blank');
    });

    addBotBtn.addEventListener('click', async () => {
        if (!bestParamsCache) { alert('請先執行優化'); return; }
        const symbol = document.getElementById('symbol-select').value;
        const timeframe = document.getElementById('timeframe-select').value;
        const strategy = strategySelect.value;

        const strategyOnlyParams = {};
        Object.keys(bestParamsCache).forEach(k => {
            if (!['risk_percent', 'sl_atr', 'tp_atr'].includes(k)) {
                strategyOnlyParams[k] = bestParamsCache[k];
            }
        });

        const botPayload = {
            name: `${symbol}_${strategy}_${timeframe}_opt`,
            market: symbol,
            risk_percent: bestParamsCache.risk_percent || 1.0,
            sl_atr_multiplier: bestParamsCache.sl_atr || 2.0,
            tp_atr_multiplier: bestParamsCache.tp_atr || 4.0,
            timeframe,
            check_interval_seconds: 1,
            strategy,
            enable_strategy_switching: true,
            params: strategyOnlyParams
        };

        try {
            addBotBtn.disabled = true;
            addBotBtn.textContent = '建立中...';
            const resp = await fetch('/api/bots', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(botPayload)
            });
            const result = await resp.json();
            if (resp.ok) {
                localStorage.setItem(BOT_KEY, JSON.stringify({
                    symbol, strategy, timeframe,
                    risk_percent: botPayload.risk_percent,
                    sl_atr_multiplier: botPayload.sl_atr_multiplier,
                    tp_atr_multiplier: botPayload.tp_atr_multiplier,
                    params: strategyOnlyParams,
                    check_interval_seconds: 1,
                    enable_strategy_switching: true
                }));
                if (typeof Toastify !== 'undefined') {
                    Toastify({ text: `機器人已建立: ${result.bot_id}`, duration: 3000, gravity: 'top', position: 'right', style: { background: '#16a34a' } }).showToast();
                } else {
                    alert(`機器人已建立: ${result.bot_id}`);
                }
            } else {
                alert(`建立失敗: ${result.error}`);
            }
        } catch (err) {
            console.error(err);
            alert('連接伺服器失敗');
        } finally {
            addBotBtn.disabled = false;
            addBotBtn.textContent = '一鍵新增機器人';
        }
    });

    loadStrategies();
});
