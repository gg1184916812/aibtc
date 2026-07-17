/**
 * AI 智慧预测引擎 - 前端逻辑 v2
 * 支持: GridSearch 训练、高级回测、交易导出、训练报告、特征重要性
 */

// ===== 全局状态 =====
let charts = {};
let logEventSource = null;
let priceTargetEventSource = null;
let backtestPollInterval = null;
let trainingPollInterval = null;
let aiBotRunning = false;

document.addEventListener('DOMContentLoaded', function() {
    initTabs();
    initAdvancedToggle();
    initTraining();
    initPrediction();
    initBacktest();
    initAIBot();
    initLogStream();
    loadModels();
    checkBotStatus();
});

// ===== Tab 切换 =====
function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.className = b.className.replace('text-purple-700 bg-white border border-b-0', 'text-gray-500 hover:text-gray-700'));
            btn.className = btn.className.replace('text-gray-500 hover:text-gray-700', 'text-purple-700 bg-white border border-b-0');
            document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
            document.getElementById('tab-' + btn.dataset.tab).classList.remove('hidden');
            if (btn.dataset.tab === 'robot') updateRobotModelList();
            if (btn.dataset.tab === 'backtest') updateBacktestModelList();
        });
    });
}

// ===== 高级参数折叠 =====
function initAdvancedToggle() {
    const btn = document.getElementById('btn-toggle-advanced');
    const panel = document.getElementById('advanced-params');
    const arrow = document.getElementById('advanced-arrow');
    if (!btn) return;
    btn.addEventListener('click', () => {
        panel.classList.toggle('hidden');
        arrow.textContent = panel.classList.contains('hidden') ? '▶' : '▼';
    });
}

// ===== 模型列表 =====
async function loadModels() {
    try {
        const resp = await fetch('/api/ai-predictor/models');
        const result = await resp.json();
        if (!result.success) return;
        renderModelList(result.data);
        updatePredictModelList(result.data);
        updateBacktestModelList();
        updateRobotModelList();
    } catch(e) { console.error(e); }
}

function renderModelList(models) {
    const container = document.getElementById('model-list');
    const search = (document.getElementById('model-search')?.value || '').toLowerCase();
    const filtered = models.filter(m => m.name.toLowerCase().includes(search) || m.symbol?.toLowerCase().includes(search));

    if (!filtered.length) {
        container.innerHTML = '<p class="text-gray-400 text-sm">暂无模型</p>';
        return;
    }

    container.innerHTML = filtered.map(m => `
        <div class="model-list-item" data-name="${m.name}" onclick="selectModel('${m.name}')">
            <div class="flex justify-between items-start">
                <div>
                    <span class="font-medium text-gray-800">${m.symbol} ${m.timeframe}</span>
                    <span class="text-xs ml-1 px-1.5 py-0.5 rounded ${m.type === 'price_target' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'}">${m.type === 'price_target' ? '目标' : '状态'}</span>
                </div>
                <span class="text-xs text-gray-400">${(m.size/1024).toFixed(0)}KB</span>
            </div>
            ${m.metrics ? `
            <div class="flex items-center space-x-3 mt-1 text-xs text-gray-500">
                <span title="准确率">Acc: ${(m.metrics.accuracy*100).toFixed(1)}%</span>
                ${m.metrics.calibrated_accuracy ? `<span title="校准后准确率">Cal: ${(m.metrics.calibrated_accuracy*100).toFixed(1)}%</span>` : ''}
                <span title="F1">F1: ${(m.metrics.f1_macro*100).toFixed(1)}%</span>
                <span title="特征数">${m.metrics.n_features || '?'} feat</span>
            </div>` : ''}
            <div class="flex space-x-2 mt-1">
                ${m.metrics ? `<button class="text-xs text-blue-500 hover:text-blue-700" onclick="event.stopPropagation();showTrainingReport('${m.name}')">📊 报告</button>` : ''}
                <button class="text-xs text-red-400 hover:text-red-600" onclick="event.stopPropagation();deleteModel('${m.name}')">🗑</button>
            </div>
        </div>
    `).join('');
}

function selectModel(name) {
    document.querySelectorAll('.model-list-item').forEach(el => el.classList.remove('selected'));
    const el = document.querySelector(`.model-list-item[data-name="${name}"]`);
    if (el) el.classList.add('selected');
    document.getElementById('predict-model').value = name;
    loadFeatureImportance(name);
}

async function deleteModel(name) {
    if (!confirm(`确定删除模型 ${name} 及其关联文件？`)) return;
    const resp = await fetch(`/api/ai-predictor/models/${encodeURIComponent(name)}`, { method: 'DELETE' });
    const result = await resp.json();
    if (result.success) {
        alert(`已删除 ${result.deleted?.length || 1} 个文件`);
        loadModels();
    } else {
        alert('删除失败: ' + (result.error || '未知错误'));
    }
}

document.getElementById('model-search')?.addEventListener('input', () => {
    loadModels().then(() => {}).catch(() => {});
});

document.getElementById('btn-refresh-models')?.addEventListener('click', loadModels);

// ===== 训练报告 =====
async function showTrainingReport(modelName) {
    try {
        const resp = await fetch(`/api/ai-predictor/models/${encodeURIComponent(modelName)}/report`);
        const result = await resp.json();
        if (!result.success) { alert('该模型没有训练报告'); return; }

        const report = result.data;
        document.getElementById('training-report-modal').classList.remove('hidden');

        // 指标卡片
        document.getElementById('report-metrics').innerHTML = `
            <div class="backtest-metric-card"><div class="label">准确率</div><div class="value positive">${(report.accuracy*100).toFixed(1)}%</div></div>
            <div class="backtest-metric-card"><div class="label">F1 Macro</div><div class="value">${(report.f1_macro*100).toFixed(1)}%</div></div>
            <div class="backtest-metric-card"><div class="label">校准准确率</div><div class="value">${report.calibrated_accuracy ? (report.calibrated_accuracy*100).toFixed(1)+'%' : 'N/A'}</div></div>
            <div class="backtest-metric-card"><div class="label">样本/特征</div><div class="value text-sm">${report.n_samples} / ${report.n_features}</div></div>
        `;

        // 混淆矩阵
        const cm = report.confusion_matrix;
        if (cm && window.Chart) {
            if (charts.confusion) charts.confusion.destroy();
            const ctx = document.getElementById('confusion-matrix-chart').getContext('2d');
            const labels = cm.map((_, i) => `Class ${i}`);
            charts.confusion = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: cm.map((row, i) => ({
                        label: `Actual ${i}`,
                        data: row,
                        backgroundColor: ['#667eea','#00b894','#e17055','#fdcb6e'][i] || '#aaa'
                    }))
                },
                options: { responsive: true, maintainAspectRatio: false, scales: { x: { stacked: true }, y: { stacked: true } }, plugins: { title: { display: true, text: '混淆矩阵' } } }
            });
        }

        // 特征重要性
        const fi = report.feature_importance?.slice(0, 10) || [];
        if (fi.length && window.Chart) {
            if (charts.reportImportance) charts.reportImportance.destroy();
            const ctx = document.getElementById('report-importance-chart').getContext('2d');
            charts.reportImportance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: fi.map(f => f.feature),
                    datasets: [{ label: '重要性', data: fi.map(f => f.importance), backgroundColor: '#764ba2' }]
                },
                options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
            });
        }

        // 分类报告表格
        const cr = report.classification_report || {};
        const rows = Object.entries(cr).filter(([k]) => k !== 'accuracy' && k !== 'macro avg' && k !== 'weighted avg').map(([k, v]) => `
            <tr><td>${k}</td><td>${v.precision?.toFixed(3) || '-'}</td><td>${v.recall?.toFixed(3) || '-'}</td><td>${v['f1-score']?.toFixed(3) || '-'}</td><td>${v.support || '-'}</td></tr>
        `).join('');
        document.getElementById('report-class-table').querySelector('tbody').innerHTML = rows;
    } catch(e) {
        console.error(e);
        alert('加载报告失败');
    }
}

// 关闭 Modal（点击外部）
document.addEventListener('click', function(e) {
    const modal = document.getElementById('training-report-modal');
    if (e.target === modal) modal.classList.add('hidden');
});

// ===== 特征重要性 =====
async function loadFeatureImportance(modelName) {
    try {
        const resp = await fetch(`/api/ai-predictor/models/${encodeURIComponent(modelName)}/report`);
        const result = await resp.json();
        if (!result.success || !result.data?.feature_importance) {
            document.getElementById('feature-importance-empty').classList.remove('hidden');
            document.getElementById('feature-importance-chart').style.display = 'none';
            return;
        }

        document.getElementById('feature-importance-empty').classList.add('hidden');
        document.getElementById('feature-importance-chart').style.display = '';

        const fi = result.data.feature_importance.slice(0, 12);
        if (charts.featureImportance) charts.featureImportance.destroy();
        const ctx = document.getElementById('feature-importance-chart').getContext('2d');
        charts.featureImportance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: fi.map(f => f.feature),
                datasets: [{ label: '特征重要性', data: fi.map(f => f.importance * 100), backgroundColor: fi.map((_, i) => ['#667eea','#764ba2','#00b894','#e17055','#fdcb6e','#00aaff','#a855f7','#ec4899','#14b8a6','#f97316','#6366f1','#84cc16'][i]) }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ctx.raw.toFixed(2) + '%' } } }
            }
        });
    } catch(e) { console.error(e); }
}

// ===== 模型列表更新 =====
function updatePredictModelList(models) {
    const sel = document.getElementById('predict-model');
    if (!models) return;
    const current = sel.value;
    sel.innerHTML = '<option value="">选择模型...</option>' +
        models.map(m => `<option value="${m.name}">${m.symbol} ${m.timeframe} (${m.type === 'price_target' ? '目标' : '状态'})</option>`).join('');
    if (models.some(m => m.name === current)) sel.value = current;
}

function updateBacktestModelList() {
    fetch('/api/ai-predictor/models').then(r => r.json()).then(result => {
        if (!result.success) return;
        const sel = document.getElementById('backtest-model');
        sel.innerHTML = '<option value="">选择模型...</option>' +
            result.data.map(m => `<option value="${m.name}">${m.symbol} ${m.timeframe} (${m.type === 'price_target' ? '目标' : '状态'})</option>`).join('');
    }).catch(() => {});
}

function updateRobotModelList() {
    fetch('/api/ai-predictor/models').then(r => r.json()).then(result => {
        if (!result.success) return;
        const sel = document.getElementById('robot-model');
        sel.innerHTML = '<option value="">选择状态预测模型</option>' +
            result.data.filter(m => m.type === 'state').map(m => `<option value="${m.name}">${m.symbol} ${m.timeframe} (Acc: ${m.metrics?.accuracy ? (m.metrics.accuracy*100).toFixed(1)+'%' : '?'})</option>`).join('');
    }).catch(() => {});
}

// ===== 训练 =====
function initTraining() {
    document.getElementById('btn-train')?.addEventListener('click', startTraining);
    document.getElementById('btn-cancel-train')?.addEventListener('click', cancelTraining);
}

async function startTraining() {
    const type = document.getElementById('train-type').value;
    const symbol = document.getElementById('train-symbol').value;
    const timeframe = document.getElementById('train-timeframe').value;
    const epochs = parseInt(document.getElementById('train-epochs').value);
    const forwardBars = parseInt(document.getElementById('train-forward-bars')?.value || 10);

    if (type === 'price_target') {
        startPriceTargetTraining(symbol, timeframe, forwardBars);
        return;
    }

    const gridSearch = document.getElementById('grid-search')?.checked || false;
    const hyperParams = {
        max_depth: parseInt(document.getElementById('hp-max-depth')?.value || 7),
        learning_rate: parseFloat(document.getElementById('hp-lr')?.value || 0.08),
        subsample: parseFloat(document.getElementById('hp-subsample')?.value || 0.8),
        colsample_bytree: parseFloat(document.getElementById('hp-colsample')?.value || 0.8),
        reg_alpha: parseFloat(document.getElementById('hp-alpha')?.value || 0.1),
    };
    const cvFolds = parseInt(document.getElementById('cv-folds')?.value || 3);

    const btn = document.getElementById('btn-train');
    btn.disabled = true;
    btn.textContent = '⏳ 训练中...';
    document.getElementById('btn-cancel-train').classList.remove('hidden');
    document.getElementById('train-progress').classList.remove('hidden');

    try {
        const resp = await fetch('/api/ai-predictor/train', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol, timeframe, epochs, forward_bars: forwardBars, grid_search: gridSearch, hyper_params: hyperParams, cv_folds: cvFolds })
        });
        const result = await resp.json();
        if (!result.success) { alert('训练启动失败: ' + (result.error || '未知')); resetTrainUI(); return; }

        trainingPollInterval = setInterval(checkTrainingStatus, 1000);
    } catch(e) {
        alert('请求失败: ' + e.message);
        resetTrainUI();
    }
}

async function startPriceTargetTraining(symbol, timeframe, forwardBars) {
    const btn = document.getElementById('btn-train');
    btn.disabled = true;
    btn.textContent = '⏳ 训练中...';
    document.getElementById('btn-cancel-train').classList.remove('hidden');
    document.getElementById('train-progress').classList.remove('hidden');

    try {
        const resp = await fetch('/api/ai-predictor/train/price-target', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol, timeframe, forward_bars: forwardBars })
        });
        const result = await resp.json();
        if (!result.success) { alert('训练启动失败'); resetTrainUI(); return; }
        trainingPollInterval = setInterval(checkTrainingStatus, 2000);
    } catch(e) {
        alert('请求失败: ' + e.message);
        resetTrainUI();
    }
}

async function checkTrainingStatus() {
    try {
        const resp = await fetch('/api/ai-predictor/train/status');
        const result = await resp.json();
        const status = result.data;

        document.getElementById('train-progress-text').textContent = status.message;
        document.getElementById('train-progress-pct').textContent = status.progress + '%';
        document.getElementById('train-progress-bar').style.width = status.progress + '%';

        if (status.done) {
            clearInterval(trainingPollInterval);
            resetTrainUI();
            if (status.error) {
                alert('训练失败: ' + status.error);
            } else {
                loadModels();
                alert('✅ 训练完成! ' + (status.model_name || ''));
                if (status.report) {
                    console.log('Training report:', status.report);
                }
            }
        }
    } catch(e) {}
}

function resetTrainUI() {
    document.getElementById('btn-train').disabled = false;
    document.getElementById('btn-train').textContent = '🚀 开始训练';
    document.getElementById('btn-cancel-train').classList.add('hidden');
}

async function cancelTraining() {
    await fetch('/api/ai-predictor/train/cancel', { method: 'POST' });
    clearInterval(trainingPollInterval);
    resetTrainUI();
}

// ===== 即时预测 =====
function initPrediction() {
    document.getElementById('btn-predict')?.addEventListener('click', doPrediction);
}

async function doPrediction() {
    const symbol = document.getElementById('predict-symbol').value;
    const model = document.getElementById('predict-model').value;
    if (!model) { alert('请先选择模型'); return; }

    document.getElementById('prediction-result').classList.add('hidden');
    document.getElementById('btn-predict').disabled = true;
    document.getElementById('btn-predict').textContent = '⏳ 预测中...';

    try {
        const resp = await fetch('/api/ai-predictor/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol, model_name: model })
        });
        const result = await resp.json();
        document.getElementById('btn-predict').disabled = false;
        document.getElementById('btn-predict').textContent = '🔍 AI 预测趋势';

        if (!result.success) { alert('预测失败: ' + (result.error || '未知')); return; }

        const d = result.data;
        document.getElementById('prediction-result').classList.remove('hidden');

        if (d.type === 'price_target') {
            document.getElementById('state-result').classList.add('hidden');
            document.getElementById('price-target-result').classList.remove('hidden');
            document.getElementById('pt-direction').textContent = d.direction || 'SIDEWAYS';
            document.getElementById('pt-target-price').textContent = '目标价: $' + (d.target_price?.toFixed(2) || '-');
            document.getElementById('pt-target-time').textContent = '预计到达: ' + (d.target_time || '-') + ' 根K线';
            document.getElementById('pt-movement').textContent = '变动: ' + (d.movement_percent?.toFixed(2) || '0') + '%';
        } else {
            document.getElementById('state-result').classList.remove('hidden');
            document.getElementById('price-target-result').classList.add('hidden');
            document.getElementById('pred-emoji').textContent = d.state_emoji || '❓';
            document.getElementById('pred-state').textContent = d.state_name || '未知';
            document.getElementById('pred-confidence').textContent = '置信度: ' + (d.confidence ? (d.confidence*100).toFixed(1)+'%' : '-');
            document.getElementById('pred-price').textContent = '当前价格: $' + (d.current_price?.toFixed(2) || '-');

            // 概率柱状图
            if (d.probabilities && d.probabilities.length) {
                if (charts.probChart) charts.probChart.destroy();
                const ctx = document.getElementById('prob-chart').getContext('2d');
                const labels = ['震荡', '多头', '空头', '突破'].slice(0, d.probabilities.length);
                charts.probChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{ label: '概率', data: d.probabilities.map(p => p*100), backgroundColor: ['#94a3b8','#00b894','#e17055','#fdcb6e'] }]
                    },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { max: 100, ticks: { callback: v => v + '%' } } } }
                });
            }
        }

        // 策略推荐
        if (d.recommended_strategy) {
            document.getElementById('rec-strategy').textContent = d.recommended_strategy;
            document.getElementById('rec-params').textContent = JSON.stringify(d.recommended_params || {});
            document.getElementById('rec-source').textContent = '推荐来源: ' + (d.recommendation_source || 'unknown');
            if (d.recommendation_win_rate) {
                document.getElementById('rec-stats').textContent = `胜率: ${d.recommendation_win_rate}% | 交易: ${d.recommendation_trades} | 回撤: ${d.recommendation_drawdown}%`;
            }
        }
    } catch(e) {
        alert('预测请求失败: ' + e.message);
        document.getElementById('btn-predict').disabled = false;
        document.getElementById('btn-predict').textContent = '🔍 AI 预测趋势';
    }
}

// ===== AI 回测 =====
function initBacktest() {
    document.getElementById('btn-backtest-start')?.addEventListener('click', startBacktest);
    document.getElementById('btn-backtest-cancel')?.addEventListener('click', cancelBacktest);
    document.getElementById('btn-backtest-export')?.addEventListener('click', exportBacktestCSV);
    document.getElementById('btn-fetch-spread')?.addEventListener('click', fetchLiveSpread);
}

async function fetchLiveSpread() {
    const symbol = document.getElementById('backtest-symbol').value;
    const btn = document.getElementById('btn-fetch-spread');
    btn.disabled = true;
    btn.textContent = '⏳ 抓取中...';
    try {
        const resp = await fetch(`/api/ai-predictor/spread?symbol=${encodeURIComponent(symbol)}`);
        const result = await resp.json();
        if (result.success && result.spread_pips != null) {
            document.getElementById('bt-spread').value = result.spread_pips;
            btn.textContent = `✅ 点差 ${result.spread_pips} 点`;
        } else {
            btn.textContent = `⚠️ ${result.error || '失败'}`;
        }
    } catch(e) {
        btn.textContent = '⚠️ 请求失败';
    }
    setTimeout(() => { btn.disabled = false; }, 2000);
}

async function startBacktest() {
    const symbol = document.getElementById('backtest-symbol').value;
    const timeframe = document.getElementById('backtest-timeframe').value;
    const model = document.getElementById('backtest-model').value;
    if (!model) { alert('请选择模型'); return; }

    const config = {
        symbol, model_name: model, timeframe,
        initial_capital: parseFloat(document.getElementById('bt-initial-capital')?.value || 10000),
        risk_percent: parseFloat(document.getElementById('bt-risk')?.value || 1.0),
        sl_atr: parseFloat(document.getElementById('bt-sl')?.value || 2.0),
        tp_atr: parseFloat(document.getElementById('bt-tp')?.value || 4.0),
        confidence_threshold: parseFloat(document.getElementById('bt-confidence')?.value || 0.55),
        prediction_interval: parseInt(document.getElementById('bt-interval')?.value || 5),
        typical_spread_pips: (() => { const v = document.getElementById('bt-spread')?.value; return v ? parseFloat(v) : null; })(),
        slippage_pips: parseFloat(document.getElementById('bt-slippage')?.value || 0.5),
        max_spread_pips: (() => { const v = document.getElementById('bt-maxspread')?.value; return v ? parseFloat(v) : null; })(),
        stop_out_ratio: parseFloat(document.getElementById('bt-stopout')?.value || 0) / 100,
    };

    document.getElementById('btn-backtest-start').classList.add('hidden');
    document.getElementById('btn-backtest-cancel').classList.remove('hidden');
    document.getElementById('backtest-result').classList.add('hidden');
    document.getElementById('backtest-logs').classList.remove('hidden');
    document.getElementById('backtest-logs').innerHTML = '<span style="color:#00aaff">⏳ 启动回测...</span>';
    document.getElementById('backtest-progress').classList.remove('hidden');
    document.getElementById('btn-backtest-export').classList.add('hidden');

    try {
        const resp = await fetch('/api/ai-predictor/backtest/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        const result = await resp.json();
        if (!result.success) { alert('回测启动失败'); resetBacktestUI(); return; }

        connectBacktestLogStream();
        backtestPollInterval = setInterval(pollBacktestStatus, 1500);
    } catch(e) {
        alert('请求失败: ' + e.message);
        resetBacktestUI();
    }
}

function connectBacktestLogStream() {
    if (priceTargetEventSource) priceTargetEventSource.close();
    priceTargetEventSource = new EventSource('/api/ai-predictor/backtest/stream');
    priceTargetEventSource.onmessage = function(event) {
        try {
            const log = JSON.parse(event.data);
            const container = document.getElementById('backtest-logs');
            
            // 根据日志类型设置颜色
            let color = '#00aaff';
            if (log.type === 'trade') {
                color = '#00ff88'; // 交易日志用绿色
            } else if (log.message.includes('❌')) {
                color = '#ff4444';
            } else if (log.message.includes('✅')) {
                color = '#00ff88';
            } else if (log.message.includes('⚠️')) {
                color = '#ffaa00';
            } else if (log.message.includes('🔄')) {
                color = '#66ccff';
            }
            
            container.innerHTML += `<div style="color:${color}">[${log.timestamp}] ${log.message}</div>`;
            container.scrollTop = container.scrollHeight;
        } catch(e) {}
    };
    priceTargetEventSource.onerror = () => { setTimeout(connectBacktestLogStream, 5000); };
}

async function pollBacktestStatus() {
    try {
        const resp = await fetch('/api/ai-predictor/backtest/status');
        const result = await resp.json();
        const s = result.data;

        if (s.progress !== undefined) {
            document.getElementById('backtest-progress-text').textContent = s.message;
            document.getElementById('backtest-progress-pct').textContent = s.progress + '%';
            document.getElementById('backtest-progress-bar').style.width = s.progress + '%';
        }

        if (s.done) {
            clearInterval(backtestPollInterval);
            if (priceTargetEventSource) priceTargetEventSource.close();
            resetBacktestUI();
            if (s.error === 'cancelled') {
                document.getElementById('backtest-logs').innerHTML += `<div style="color:#ffaa00">🛑 回测已取消</div>`;
            } else if (s.error) {
                document.getElementById('backtest-logs').innerHTML += `<div style="color:#ff4444">❌ 回测失败: ${s.error}</div>`;
            } else if (s.result) {
                displayBacktestResult(s.result);
            } else {
                document.getElementById('backtest-logs').innerHTML += `<div style="color:#ffaa00">⚠️ 回测结束，但没有可显示的结果</div>`;
            }
        }
    } catch(e) {}
}

function displayBacktestResult(data) {
    document.getElementById('backtest-result').classList.remove('hidden');
    document.getElementById('btn-backtest-export').classList.remove('hidden');

    // 关键指标
    const metrics = [
        { label: '总盈亏', value: '$' + (data.total_profit||0).toFixed(0), cls: data.total_profit >= 0 ? 'positive' : 'negative' },
        { label: '收益率', value: (data.total_profit_percent||0).toFixed(1) + '%', cls: data.total_profit_percent >= 0 ? 'positive' : 'negative' },
        { label: '胜率', value: (data.win_rate||0).toFixed(1) + '%', cls: '' },
        { label: '夏普比率', value: (data.sharpe_ratio||0).toFixed(2), cls: '' },
        { label: 'Calmar', value: (data.calmar_ratio||0).toFixed(2), cls: '' },
        { label: '最大回撤', value: (data.max_drawdown||0).toFixed(1) + '%', cls: 'negative' },
        { label: '盈亏比', value: typeof data.profit_factor === 'number' ? data.profit_factor.toFixed(2) : (data.profit_factor || '-'), cls: '' },
        { label: '总交易', value: data.total_trades || 0, cls: '' },
        { label: '盈利/亏损', value: `${data.winning_trades||0} / ${data.losing_trades||0}`, cls: '' },
        { label: '最大连胜', value: data.max_consecutive_wins || 0, cls: 'positive' },
        { label: '最大连亏', value: data.max_consecutive_losses || 0, cls: 'negative' },
        { label: '平均盈亏', value: '$' + ((data.avg_win||0)-(data.avg_loss||0)).toFixed(1), cls: '' },
    ];
    document.getElementById('backtest-metrics').innerHTML = metrics.map(m => `
        <div class="backtest-metric-card"><div class="label">${m.label}</div><div class="value ${m.cls}">${m.value}</div></div>
    `).join('');

    // 权益曲线
    drawChart('backtest-equity-chart', 'equity', {
        type: 'line',
        data: {
            labels: (data.equity_curve||[]).map(e => e.time || ''),
            datasets: [{ label: '权益', data: (data.equity_curve||[]).map(e => e.capital || e.equity || 0), borderColor: '#667eea', fill: false, tension: 0.1, pointRadius: 0 }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { ticks: { callback: v => '$' + v.toFixed(0) } } } }
    });

    // 回撤曲线
    const equity = (data.equity_curve||[]).map(e => e.capital || e.equity || 0);
    const drawdowns = [];
    let peak = equity[0] || 0;
    equity.forEach(e => {
        if (e > peak) peak = e;
        drawdowns.push(peak > 0 ? -((peak - e) / peak * 100) : 0);
    });
    drawChart('backtest-drawdown-chart', 'drawdown', {
        type: 'line',
        data: {
            labels: (data.equity_curve||[]).map(e => e.time || ''),
            datasets: [{ label: '回撤%', data: drawdowns, borderColor: '#e17055', backgroundColor: 'rgba(225,112,85,0.1)', fill: true, tension: 0.1, pointRadius: 0 }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { ticks: { callback: v => v + '%' } } } }
    });

    // 策略切换时间线
    const switches = data.strategy_switches || [];
    if (switches.length) {
        drawChart('backtest-switches-chart', 'switches', {
            type: 'bar',
            data: {
                labels: switches.map(s => s.time || ''),
                datasets: [{ label: '策略', data: switches.map((_, i) => i + 1), backgroundColor: ['#667eea','#00b894','#e17055','#fdcb6e','#764ba2','#00aaff'], barThickness: 8 }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => switches[ctx.dataIndex]?.strategy || '' } } } }
        });
    } else {
        document.getElementById('backtest-switches-chart').parentElement.innerHTML = '<div class="text-sm text-gray-400 text-center py-8">本次回测無策略切換記錄</div>';
    }

    // 策略分布
    const switchStats = data.switches_by_strategy || {};
    const strategyUsage = data.strategy_usage || {};
    if (Object.keys(switchStats).length || Object.keys(strategyUsage).length) {
        let html = '';
        if (Object.keys(switchStats).length) {
            html += Object.entries(switchStats).map(([k, v]) => `<div class="flex justify-between"><span class="text-gray-600">${k} (切換)</span><span class="font-medium">${v} 次</span></div>`).join('');
        }
        if (Object.keys(strategyUsage).length) {
            html += Object.entries(strategyUsage).map(([k, v]) => `<div class="flex justify-between"><span class="text-gray-600">${k} (使用)</span><span class="font-medium">${v} 根K线</span></div>`).join('');
        }
        document.getElementById('backtest-switches-stats').innerHTML = html;
    } else {
        document.getElementById('backtest-switches-stats').innerHTML = '<div class="text-sm text-gray-400 text-center py-4">無策略數據</div>';
    }

    // 交易明细
    const trades = (data.trades || []).filter(t => t.action === 'CLOSE').slice(-50);
    if (trades.length) {
        document.getElementById('backtest-trades-table').querySelector('tbody').innerHTML = trades.map(t => `
            <tr>
                <td>${t.time || '-'}</td>
                <td><span class="${t.profit > 0 ? 'text-green-600' : 'text-red-600'}">${t.direction || '-'}</span></td>
                <td>$${t.entry_price?.toFixed(2) || '-'}</td>
                <td>$${t.exit_price?.toFixed(2) || '-'}</td>
                <td>${(t.lot_size ?? t.lotSize ?? 0).toFixed(3)}</td>
                <td class="${t.profit > 0 ? 'text-green-600' : 'text-red-600'}">${t.profit ? '$'+t.profit.toFixed(2) : '-'}</td>
                <td class="text-blue-600">$${(t.remaining_balance ?? t.capital ?? 0).toFixed(2)}</td>
                <td class="text-xs text-gray-500">${t.strategy || '-'}</td>
            </tr>
        `).join('');
    } else {
        document.getElementById('backtest-trades-table').querySelector('tbody').innerHTML = '<tr><td colspan="8" class="text-center text-gray-400 py-4">本次回测無交易記錄</td></tr>';
    }
}

function drawChart(canvasId, chartKey, config) {
    if (charts[chartKey]) charts[chartKey].destroy();
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    charts[chartKey] = new Chart(canvas.getContext('2d'), config);
}

function resetBacktestUI() {
    document.getElementById('btn-backtest-start').classList.remove('hidden');
    document.getElementById('btn-backtest-cancel').classList.add('hidden');
    document.getElementById('backtest-progress').classList.add('hidden');
}

async function cancelBacktest() {
    try {
        await fetch('/api/ai-predictor/backtest/cancel', { method: 'POST' });
    } catch(e) {}
    clearInterval(backtestPollInterval);
    if (priceTargetEventSource) priceTargetEventSource.close();
    resetBacktestUI();
}

function exportBacktestCSV() {
    const result = document.getElementById('backtest-result');
    if (result.classList.contains('hidden')) return;
    const rows = document.querySelectorAll('#backtest-trades-table tbody tr');
    if (!rows.length) return;

    let csv = '时间,方向,入场价,出场价,手数,盈亏,平仓后余额,策略\n';
    rows.forEach(tr => {
        const tds = tr.querySelectorAll('td');
        csv += Array.from(tds).map(td => td.textContent).join(',') + '\n';
    });

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'backtest_trades_' + new Date().toISOString().slice(0,10) + '.csv';
    a.click();
    URL.revokeObjectURL(url);
}

// ===== AI 机器人 =====
function initAIBot() {
    document.getElementById('btn-ai-bot')?.addEventListener('click', toggleAIBot);
}

async function toggleAIBot() {
    const btn = document.getElementById('btn-ai-bot');
    const model = document.getElementById('robot-model').value;

    if (aiBotRunning) {
        btn.disabled = true;
        btn.textContent = '⏳ 停止中...';
        const resp = await fetch('/api/ai-predictor/bot/stop', { method: 'POST' });
        const result = await resp.json();
        if (result.success) {
            aiBotRunning = false;
            updateBotUI(false);
        }
        btn.disabled = false;
        return;
    }

    if (!model) { alert('请选择模型'); return; }
    if (model.includes('price_target')) { alert('AI机器人仅支持状态预测模型'); return; }

    btn.disabled = true;
    btn.textContent = '⏳ 启动中...';

    try {
        const risk = parseFloat(document.getElementById('robot-risk')?.value || 0.5);
        const confidence = parseFloat(document.getElementById('robot-confidence')?.value || 0.55);

        const resp = await fetch('/api/ai-predictor/bot/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                symbol: model.split('_')[0] || 'XAUUSDm',
                model_name: model,
                risk_percent: risk,
                confidence_threshold: confidence,
            })
        });
        const result = await resp.json();
        if (result.success) {
            aiBotRunning = true;
            updateBotUI(true);
            document.getElementById('bot-status-message').textContent = 'AI 机器人运行中...';
        } else {
            alert('启动失败: ' + (result.error || '未知'));
        }
    } catch(e) {
        alert('请求失败: ' + e.message);
    }
    btn.disabled = false;
}

function updateBotUI(running) {
    const btn = document.getElementById('btn-ai-bot');
    const dot = document.getElementById('bot-status-dot');
    const text = document.getElementById('bot-status-text');

    if (running) {
        dot.className = 'status-dot running';
        text.textContent = '运行中';
        btn.textContent = '🔴 停止 AI 机器人';
        btn.className = 'w-full btn-ai-stop';
    } else {
        dot.className = 'status-dot stopped';
        text.textContent = '已停止';
        btn.textContent = '🟢 启动 AI 机器人';
        btn.className = 'w-full btn-ai-start';
    }
}

async function checkBotStatus() {
    try {
        const resp = await fetch('/api/ai-predictor/bot/status');
        const result = await resp.json();
        if (result.success) {
            aiBotRunning = result.data?.is_running || false;
            updateBotUI(aiBotRunning);
            if (aiBotRunning && result.data) {
                document.getElementById('bot-metrics').innerHTML = `
                    <div class="flex justify-between"><span>当前状态</span><span class="font-medium">${result.data.state || '-'}</span></div>
                    <div class="flex justify-between"><span>策略</span><span class="font-medium">${result.data.strategy || '-'}</span></div>
                    <div class="flex justify-between"><span>置信度</span><span class="font-medium">${result.data.confidence ? (result.data.confidence*100).toFixed(1)+'%' : '-'}</span></div>
                    <div class="flex justify-between"><span>持仓</span><span class="font-medium ${result.data.has_position ? 'text-green-600' : ''}">${result.data.has_position ? '有' : '无'}</span></div>
                    <div class="flex justify-between"><span>运行时长</span><span class="font-medium text-xs">${result.data.running_since || '-'}</span></div>
                `;
            }
        }
    } catch(e) {}
    setTimeout(checkBotStatus, 10000);
}

// ===== 日志流 =====
function initLogStream() {
    connectLogStream();
    document.getElementById('btn-clear-logs')?.addEventListener('click', () => {
        document.getElementById('log-output').innerHTML = '<span class="log-info">📋 日志已清空</span>';
    });
}

function connectLogStream() {
    if (logEventSource) logEventSource.close();
    logEventSource = new EventSource('/api/ai-predictor/bot/logs/stream');
    logEventSource.onmessage = function(event) {
        try {
            const log = JSON.parse(event.data);
            const container = document.getElementById('log-output');
            const cls = 'log-' + (log.level || 'info');
            container.innerHTML += `<div class="${cls}">[${log.timestamp}] ${log.message}</div>`;
            container.scrollTop = container.scrollHeight;
            if (container.children.length > 200) {
                while (container.children.length > 150) container.removeChild(container.firstChild);
            }
        } catch(e) {}
    };
    logEventSource.onerror = () => { setTimeout(connectLogStream, 5000); };
}
