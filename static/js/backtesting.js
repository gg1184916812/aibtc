// static/js/backtesting.js
document.addEventListener('DOMContentLoaded', () => {
    const strategySelect = document.getElementById('strategy-select');
    const paramsContainer = document.getElementById('params-container');
    const form = document.getElementById('backtest-form');
    const runBtn = document.getElementById('run-backtest-btn');
    const resultsContainer = document.getElementById('results-container');
    const resultsSummary = document.getElementById('results-summary');
    const loadingSpinner = document.getElementById('loading-spinner');
    const resultsLog = document.getElementById('results-log');
    const downloadProgress = document.getElementById('download-progress');
    const downloadStatus = document.getElementById('download-status');
    const downloadBar = document.getElementById('download-bar');
    const addBotBtn = document.getElementById('add-bot-from-backtest');
    const presetSelect = document.getElementById('preset-select');
    const applyPresetBtn = document.getElementById('apply-preset-btn');
    const presetSource = document.getElementById('preset-source');
    const aiModelSelect = document.getElementById('ai-model-select'); // New: Get AI model select element
    let equityChart = null;
    let lastBacktestParams = null;

    const STORAGE_KEY = 'quantumBotX_backtest_defaults';

    setDefaultDateRange();
    loadDefaults();

    function setDefaultDateRange() {
        const today = new Date();
        const oneMonthAgo = new Date(today);
        oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);
        if (!document.getElementById('date-from').value) {
            document.getElementById('date-from').value = oneMonthAgo.toISOString().split('T')[0];
        }
        if (!document.getElementById('date-to').value) {
            document.getElementById('date-to').value = today.toISOString().split('T')[0];
        }
    }

    function loadDefaults() {
        try {
            const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
            if (saved) {
                if (saved.symbol) document.getElementById('symbol-select').value = saved.symbol;
                if (saved.timeframe) document.getElementById('timeframe-select').value = saved.timeframe;
                if (saved.risk_percent != null) document.getElementById('risk_percent').value = saved.risk_percent;
                if (saved.sl_atr_multiplier != null) document.getElementById('sl_atr_multiplier').value = saved.sl_atr_multiplier;
                if (saved.tp_atr_multiplier != null) document.getElementById('tp_atr_multiplier').value = saved.tp_atr_multiplier;
                if (saved.initial_capital != null) document.getElementById('initial_capital').value = saved.initial_capital;
                // New: Load saved AI model selection
                if (saved.ai_model) aiModelSelect.value = saved.ai_model;
            }
        } catch (e) {
            // ignore
        }
    }

    async function loadStrategies() {
        try {
            const response = await fetch('/api/strategies');
            if (!response.ok) throw new Error('載入策略失敗');
            const strategies = await response.json();

            strategySelect.innerHTML = '<option value="" disabled selected>請選擇策略</option>';
            strategies.forEach(strategy => {
                const option = document.createElement('option');
                option.value = strategy.id;
                option.textContent = strategy.name;
                strategySelect.appendChild(option);
            });

            const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
            if (saved.strategy && strategySelect.querySelector(`option[value="${saved.strategy}"]`)) {
                strategySelect.value = saved.strategy;
                strategySelect.dispatchEvent(new Event('change'));
            }
        } catch (error) {
            console.error('Error loading strategies:', error);
            strategySelect.innerHTML = '<option value="">載入策略失敗</option>';
        }
    }

    // New: Function to load AI models
    async function loadAIModels() {
        try {
            const response = await fetch('/api/ai-predictor/models');
            if (!response.ok) throw new Error('載入 AI 模型失敗');
            const models = await response.json();

            aiModelSelect.innerHTML = '<option value="">不使用 AI 預測</option>'; // Default option
            models.data.forEach(model => {
                const option = document.createElement('option');
                option.value = model.name;
                option.textContent = `[${model.type === 'price_target' ? '目標價' : '狀態'}] ${model.name} (${model.symbol}_${model.timeframe})`;
                aiModelSelect.appendChild(option);
            });

            const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
            if (saved.ai_model && aiModelSelect.querySelector(`option[value="${saved.ai_model}"]`)) {
                aiModelSelect.value = saved.ai_model;
            }
        } catch (error) {
            console.error('Error loading AI models:', error);
            // Optionally, disable the AI model select or show an error message
        }
    }

    strategySelect.addEventListener('change', async () => {
        const strategyId = strategySelect.value;
        paramsContainer.innerHTML = '<p class="text-sm text-gray-500">載入參數中...</p>';
        if (!strategyId) {
            paramsContainer.innerHTML = '';
            return;
        }

        try {
            const res = await fetch(`/api/strategies/${strategyId}/params`);
            const params = await res.json();
            paramsContainer.innerHTML = '';

            const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
            const savedParams = saved.params || {};

            if (params.length > 0) {
                params.forEach(param => {
                    const savedVal = savedParams[param.name];
                    const val = savedVal != null ? savedVal : param.default;
                    paramsContainer.innerHTML += `
                        <div>
                            <label for="${param.name}" class="block text-sm font-medium text-gray-700">${param.label}</label>
                            <input type="${param.type || 'number'}" name="${param.name}" id="${param.name}" value="${val}" step="${param.step || 'any'}" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm">
                        </div>`;
                });
            } else {
                paramsContainer.innerHTML = '<p class="text-sm text-gray-500">此策略無自定義參數</p>';
            }
        } catch (err) {
            console.error('載入策略參數失敗:', err);
            paramsContainer.innerHTML = '<p class="text-sm text-red-500">載入參數失敗</p>';
        }
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const symbol = document.getElementById('symbol-select').value;
        const timeframe = document.getElementById('timeframe-select').value;
        const dateFrom = document.getElementById('date-from').value;
        const dateTo = document.getElementById('date-to').value;
        const strategy = strategySelect.value;
        const aiModel = aiModelSelect.value; // New: Get selected AI model

        if (!strategy) {
            alert('請選擇策略');
            return;
        }
        if (!dateFrom || !dateTo) {
            alert('請選擇日期範圍');
            return;
        }
        if (dateFrom >= dateTo) {
            alert('開始日期必須早於結束日期');
            return;
        }

        loadingSpinner.classList.remove('hidden');
        resultsContainer.classList.add('hidden');
        addBotBtn.classList.add('hidden');
        downloadProgress.classList.remove('hidden');
        runBtn.disabled = true;
        runBtn.textContent = '執行中...';
        downloadStatus.textContent = '正在從MT5下載歷史數據...';
        downloadBar.style.width = '20%';

        const params = {};
        params['risk_percent'] = parseFloat(document.getElementById('risk_percent').value) || 1.0;
        params['sl_pips'] = parseFloat(document.getElementById('sl_atr_multiplier').value);
        params['tp_pips'] = parseFloat(document.getElementById('tp_atr_multiplier').value);
        paramsContainer.querySelectorAll('input').forEach(input => {
            const value = parseFloat(input.value);
            params[input.name] = isNaN(value) ? input.value : value;
        });

        lastBacktestParams = {
            symbol,
            timeframe,
            dateFrom,
            dateTo,
            strategy,
            risk_percent: params.risk_percent,
            sl_atr_multiplier: params.sl_pips,
            tp_atr_multiplier: params.tp_pips,
            strategyParams: {}
        };
        paramsContainer.querySelectorAll('input').forEach(input => {
            const value = parseFloat(input.value);
            lastBacktestParams.strategyParams[input.name] = isNaN(value) ? input.value : value;
        });

        const payload = { symbol, timeframe, date_from: dateFrom, date_to: dateTo, strategy, params,
            initial_capital: parseFloat(document.getElementById('initial_capital').value) || 100,
            model_name: aiModel // New: Include selected AI model name
        };

        try {
            downloadStatus.textContent = '數據下載完成，正在執行回測...';
            downloadBar.style.width = '60%';

            const response = await fetch('/api/backtest/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const results = await response.json();

            downloadBar.style.width = '100%';

            if (response.ok) {
                displayResults(results, symbol, timeframe, strategy);
            } else {
                alert(`錯誤: ${results.error}`);
            }
        } catch (err) {
            console.error("Backtest failed:", err);
            alert('連接伺服器失敗');
        } finally {
            setTimeout(() => {
                downloadProgress.classList.add('hidden');
                loadingSpinner.classList.add('hidden');
                downloadBar.style.width = '0%';
                runBtn.disabled = false;
                runBtn.textContent = '執行回測';
            }, 500);
        }
    });

    function displayResults(data, symbol, timeframe, strategyId) {
        resultsContainer.classList.remove('hidden');
        addBotBtn.classList.remove('hidden');

        const spreadCosts = data.total_spread_costs ?? 0;
        const netProfit = data.net_profit_after_costs ?? data.total_profit_usd ?? 0;
        const grossProfit = data.gross_profit_usd ?? (netProfit + spreadCosts);
        const instrument = data.instrument || symbol;

        const engineConfig = data.engine_config || {};
        const instrumentConfig = engineConfig.instrument_config || {};
        const maxRisk = instrumentConfig.max_risk_percent || 2.0;
        const spreadPips = data.actual_spread_pips || instrumentConfig.typical_spread_pips || 2.0;
        const pipSize = data.pip_size || 0.01;

        if (lastBacktestParams) {
            lastBacktestParams.strategy = strategyId;
            lastBacktestParams.symbol = symbol;
            lastBacktestParams.timeframe = timeframe;
        }

        resultsSummary.innerHTML = `
            <div class="p-4 bg-gray-50 rounded-lg">
                <p class="text-sm text-gray-500">交易品種</p>
                <p class="text-lg font-bold text-blue-600">${instrument}</p>
                <p class="text-xs text-gray-400">週期: ${timeframe}</p>
            </div>
            <div class="p-4 bg-gray-50 rounded-lg">
                <p class="text-sm text-gray-500">毛利潤</p>
                <p class="text-2xl font-bold ${grossProfit >= 0 ? 'text-green-600' : 'text-red-600'}">${grossProfit.toFixed(2)} $</p>
                <p class="text-xs text-gray-400">未扣除成本</p>
            </div>
            <div class="p-4 bg-gray-50 rounded-lg">
                <p class="text-sm text-gray-500">點差成本</p>
                <p class="text-2xl font-bold text-red-600">-${spreadCosts.toFixed(2)} $</p>
                <p class="text-xs text-gray-400">實際點差: ${spreadPips} 點 | 每點: ${pipSize}</p>
            </div>
            <div class="p-4 bg-gray-50 rounded-lg">
                <p class="text-sm text-gray-500">淨利潤</p>
                <p class="text-2xl font-bold ${netProfit >= 0 ? 'text-green-600' : 'text-red-600'}">${netProfit.toFixed(2)} $</p>
                <p class="text-xs text-gray-400">扣除所有成本後</p>
            </div>
            <div class="p-4 bg-gray-50 rounded-lg">
                <p class="text-sm text-gray-500">最大回撤</p>
                <p class="text-2xl font-bold text-red-600">${data.max_drawdown_percent.toFixed(2)}%</p>
            </div>
            <div class="p-4 bg-gray-50 rounded-lg">
                <p class="text-sm text-gray-500">勝率</p>
                <p class="text-2xl font-bold text-blue-600">${data.win_rate_percent.toFixed(2)}%</p>
            </div>
            <div class="p-4 bg-gray-50 rounded-lg">
                <p class="text-sm text-gray-500">總交易次數</p>
                <p class="text-2xl font-bold">${data.total_trades}</p>
                <p class="text-xs text-gray-400">最大風險: ${maxRisk}%</p>
            </div>
            <div class="p-4 bg-gray-50 rounded-lg">
                <p class="text-sm text-gray-500">盈利次數</p>
                <p class="text-2xl font-bold">${data.wins}</p>
            </div>
            <div class="p-4 bg-gray-50 rounded-lg">
                <p class="text-sm text-gray-500">虧損次數</p>
                <p class="text-2xl font-bold">${data.losses}</p>
            </div>
        `;

        displayEquityChart(data.equity_curve);

        if (data.trades && data.trades.length > 0) {
            let logHtml = '<h4 class="text-lg font-semibold mt-6 mb-2">最近 20 筆交易</h4>';
            logHtml += '<div class="text-xs font-mono border rounded p-2 bg-gray-50 max-h-64 overflow-y-auto">';

            data.trades.slice(-20).reverse().forEach(trade => {
                const profitClass = trade.profit > 0 ? 'text-green-600' : 'text-red-600';
                const spreadCost = trade.spread_cost || 0;
                const lotSize = trade.lot_size || 0;
                const reason = trade.reason || 'N/A';

                logHtml += `<p class="mb-1">`;
                logHtml += `<span class="font-bold">${trade.position_type}</span> | `;
                logHtml += `入場: ${(trade.entry || 0).toFixed(4)} | `;
                logHtml += `出場: ${(trade.exit || 0).toFixed(4)} | `;
                logHtml += `手數: ${lotSize.toFixed(2)} | `;
                logHtml += `盈虧: <span class="${profitClass}">$${trade.profit.toFixed(2)}</span> | `;
                logHtml += `點差: $${spreadCost.toFixed(2)} | `;
                logHtml += `原因: ${reason}`;
                logHtml += `</p>`;
            });

            logHtml += '</div>';
            resultsLog.innerHTML = logHtml;
        } else {
            resultsLog.innerHTML = '<p class="text-gray-500 text-center py-4">無交易記錄</p>';
        }
    }

    addBotBtn.addEventListener('click', async () => {
        if (!lastBacktestParams) {
            alert('請先執行回測');
            return;
        }

        const p = lastBacktestParams;
        const botPayload = {
            name: `${p.symbol}_${p.strategy}_${p.timeframe}`,
            market: p.symbol,
            risk_percent: p.risk_percent,
            sl_atr_multiplier: p.sl_atr_multiplier,
            tp_atr_multiplier: p.tp_atr_multiplier,
            timeframe: p.timeframe,
            check_interval_seconds: 1,
            strategy: p.strategy,
            enable_strategy_switching: true,
            params: p.strategyParams || {}
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
                saveBotDefaults(botPayload);
                if (typeof Toastify !== 'undefined') {
                    Toastify({ text: `機器人已建立: ${result.bot_id}`, duration: 3000, gravity: 'top', position: 'right', style: { background: '#16a34a' } }).showToast();
                } else {
                    alert(`機器人已建立: ${result.bot_id}`);
                }
            } else {
                alert(`建立失敗: ${result.error}`);
            }
        } catch (err) {
            console.error('建立機器人失敗:', err);
            alert('連接伺服器失敗');
        } finally {
            addBotBtn.disabled = false;
            addBotBtn.textContent = '一鍵新增機器人';
        }
    });

    function saveBotDefaults(botPayload) {
        try {
            const defaults = {
                symbol: botPayload.market,
                strategy: botPayload.strategy,
                timeframe: botPayload.timeframe,
                risk_percent: botPayload.risk_percent,
                sl_atr_multiplier: botPayload.sl_atr_multiplier,
                tp_atr_multiplier: botPayload.tp_atr_multiplier,
                check_interval_seconds: 1,
                enable_strategy_switching: true,
                params: botPayload.params
            };
            localStorage.setItem('quantumBotX_bot_defaults', JSON.stringify(defaults));
        } catch (e) {
            // ignore
        }
    }

    function displayEquityChart(equityData) {
        const ctx = document.getElementById('equity-chart').getContext('2d');
        if (equityChart) {
            equityChart.destroy();
        }
        equityChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: Array.from({ length: equityData.length }, (_, i) => i + 1),
                datasets: [{
                    label: '權益曲線',
                    data: equityData,
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1,
                    pointRadius: 0,
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false },
                    title: { display: true, text: '權益曲線' }
                },
                scales: { y: { beginAtZero: false } }
            }
        });
    }

    // ============================================================
    // Presets
    // ============================================================

    async function loadPresets() {
        const symbol = document.getElementById('symbol-select').value;
        const strategy = strategySelect.value;
        if (!strategy) { presetSelect.innerHTML = '<option value="">— 先選策略 —</option>'; applyPresetBtn.disabled = true; return; }
        try {
            const resp = await fetch(`/api/presets?symbol=${symbol}&strategy=${strategy}`);
            const data = await resp.json();
            const presets = data.presets || [];
            presetSelect.innerHTML = '<option value="">— 選一個預設參數 —</option>';
            presets.forEach((p, i) => {
                const opt = document.createElement('option');
                opt.value = i;
                opt.textContent = p.name;
                presetSelect.appendChild(opt);
            });
            applyPresetBtn.disabled = presets.length === 0;
            presetSelect._presets = presets;
            presetSource.textContent = '';
        } catch (err) {
            console.error('Presets load error:', err);
        }
    }

    function applyPreset() {
        const idx = parseInt(presetSelect.value);
        if (isNaN(idx)) return;
        const presets = presetSelect._presets || [];
        const p = presets[idx];
        if (!p) return;

        // Apply risk params
        if (p.risk_percent !== undefined) document.getElementById('risk_percent').value = p.risk_percent;
        if (p.sl_atr !== undefined) document.getElementById('sl_atr_multiplier').value = p.sl_atr;
        if (p.tp_atr !== undefined) document.getElementById('tp_atr_multiplier').value = p.tp_atr;

        // Apply strategy params
        const params = p.params || {};
        document.querySelectorAll('#params-container input[type="number"]').forEach(el => {
            const name = el.getAttribute('data-param-name') || el.name;
            if (params[name] !== undefined) {
                el.value = params[name];
            }
        });

        // Show source
        if (p.source) {
            presetSource.textContent = `${p.source}${p.note ? ' — ' + p.note : ''}`;
        }

        if (typeof Toastify !== 'undefined') {
            Toastify({ text: `已套用：${p.name}`, duration: 3000, gravity: 'top', position: 'right', style: { background: '#16a34a' } }).showToast();
        }
    }

    presetSelect.addEventListener('change', () => {
        applyPresetBtn.disabled = !presetSelect.value;
    });
    applyPresetBtn.addEventListener('click', applyPreset);

    // Reload presets when strategy or symbol changes
    const origStrategyChange = strategySelect.onchange;
    strategySelect.addEventListener('change', loadPresets);
    document.getElementById('symbol-select').addEventListener('change', loadPresets);

    loadStrategies();
    loadAIModels(); // New: Load AI models on startup
});
