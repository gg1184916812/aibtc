// static/js/bot_detail.js - VERSI PERBAIKAN FINAL DENGAN AI PREDICTION

document.addEventListener('DOMContentLoaded', function() {
    // --- Elemen Global ---
    const botNameHeader = document.getElementById('bot-name-header');
    const botMarketHeader = document.getElementById('bot-market-header');
    const botStatusBadge = document.getElementById('bot-status-badge');
    const paramsContainer = document.getElementById('bot-parameters-container');
    const analysisContainer = document.getElementById('bot-analysis-container');
    const analysisSignal = document.getElementById('analysis-signal');
    const historyContainer = document.getElementById('history-log-container');

    // --- State & Helper ---
    const pathParts = window.location.pathname.split('/');
    const botId = pathParts[pathParts.length - 1];
    let botData = null; 

    const formatTimestamp = (iso) =>
        new Date(iso).toLocaleString('id-ID', {
            day: '2-digit', month: 'short', year: 'numeric',
            hour: '2-digit', minute: '2-digit', second: '2-digit'
        });

    // --- Fungsi Pengambil Data ---

    async function fetchBotDetails() {
        try {
            const res = await fetch(`/api/bots/${botId}`);
            if (!res.ok) throw new Error('Gagal memuat detail bot dari server.');
            botData = await res.json();
            if (botData.error) throw new Error(botData.error);

            // Render detail bot
            botNameHeader.textContent = botData.name;
            botMarketHeader.textContent = `Pasar: ${botData.market} | Timeframe: ${botData.timeframe}`;
            botStatusBadge.textContent = botData.status;

            // Render Parameter Standar
            let paramsHTML = `
                <div class="grid grid-cols-2 gap-4">
                    <div><p class="text-gray-500">Risk per Trade</p><p class="font-semibold text-gray-800">${botData.lot_size}%</p></div>
                    <div><p class="text-gray-500">SL (ATR Multiplier)</p><p class="font-semibold text-gray-800">${botData.sl_pips}x ATR</p></div>
                    <div><p class="text-gray-500">TP (ATR Multiplier)</p><p class="font-semibold text-gray-800">${botData.tp_pips}x ATR</p></div>
                    <div><p class="text-gray-500">Interval</p><p class="font-semibold text-gray-800">${botData.check_interval_seconds}s</p></div>
                </div>
            `;

            // Render Parameter Strategi Kustom jika ada
            const customParams = botData.strategy_params || {};
            const customParamKeys = Object.keys(customParams);

            if (customParamKeys.length > 0) {
                paramsHTML += '<div class="border-t mt-4 pt-3"><h4 class="text-sm font-semibold text-gray-700 mb-2">Parameter Strategi</h4><div class="grid grid-cols-2 gap-4">';
                customParamKeys.forEach(key => {
                    const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                    paramsHTML += `<div><p class="text-gray-500">${label}</p><p class="font-semibold text-gray-800">${customParams[key]}</p></div>`;
                });
                paramsHTML += '</div></div>';
            }
            paramsContainer.innerHTML = paramsHTML;
            
        } catch (e) {
            console.error('Error fetching bot details:', e);
            botNameHeader.textContent = 'Gagal Memuat';
            paramsContainer.innerHTML = '<p class="text-center text-red-500">Gagal memuat parameter.</p>';
        }
    }

    async function fetchBotHistory() {
        try {
            const res = await fetch(`/api/bots/${botId}/history`);
            const history = await res.json();
            historyContainer.innerHTML = '';

            if (history.length === 0) {
                historyContainer.innerHTML = '<p class="text-gray-500 p-4 text-center">Belum ada aktivitas.</p>';
                return;
            }

            history.forEach(log => {
                let icon = 'fa-info-circle text-blue-500';
                if (log.action.includes('BELI')) icon = 'fa-arrow-up text-green-500';
                if (log.action.includes('JUAL')) icon = 'fa-arrow-down text-red-500';

                historyContainer.innerHTML += `
                    <div class="flex items-start p-3 border-b border-gray-100">
                        <i class="fas ${icon} mt-1 mr-3"></i>
                        <div class="flex-1">
                            <p class="text-sm text-gray-800">${log.details}</p>
                            <p class="text-xs text-gray-400 mt-1">${formatTimestamp(log.timestamp)}</p>
                        </div>
                    </div>`;
            });
        } catch (e) {
            console.error('Error fetching history:', e);
            historyContainer.innerHTML = '<p class="text-center text-red-500">Gagal memuat riwayat.</p>';
        }
    }

    async function fetchAndDisplayAnalysis() {
        try {
            const res = await fetch(`/api/bots/${botId}/analysis`);
            if (!res.ok) throw new Error('Gagal memuat data analisis.');
            const analysis = await res.json();

            const signal = (analysis.signal || "TAHAN").toUpperCase();
            analysisSignal.textContent = signal;
            let color = 'bg-gray-200 text-gray-800';
            if (signal.includes('BUY')) color = 'bg-green-100 text-green-800';
            else if (signal.includes('SELL')) color = 'bg-red-100 text-red-800';
            analysisSignal.className = `mt-4 text-center font-bold text-lg p-2 rounded-md ${color}`;

            // Kosongkan container
            analysisContainer.innerHTML = "";

            // ====== 1. AI PREDICTION CARD ======
            if (analysis.ai_state !== undefined && analysis.ai_state !== null) {
                const stateMap = {
                    0: { label: '🔄 震荡', color: 'bg-gray-100 text-gray-700', border: 'border-gray-300' },
                    1: { label: '📈 多头趋势', color: 'bg-green-100 text-green-700', border: 'border-green-300' },
                    2: { label: '📉 空头趋势', color: 'bg-red-100 text-red-700', border: 'border-red-300' },
                    3: { label: '⚡ 高波动突破', color: 'bg-yellow-100 text-yellow-700', border: 'border-yellow-300' }
                };
                const stateInfo = stateMap[analysis.ai_state] || stateMap[0];
                const confidence = (analysis.ai_confidence * 100).toFixed(1);
                const proba = analysis.ai_probabilities || [];
                
                let probaHtml = '';
                if (proba.length === 4) {
                    const stateLabels = ['震荡', '多头', '空头', '突破'];
                    const stateColors = ['bg-gray-200', 'bg-green-200', 'bg-red-200', 'bg-yellow-200'];
                    probaHtml = `<div class="flex gap-1 mt-2 text-xs flex-wrap">
                        ${proba.map((p, i) => `
                            <span class="px-2 py-0.5 rounded ${stateColors[i]}">${stateLabels[i]} ${(p*100).toFixed(0)}%</span>
                        `).join('')}
                    </div>`;
                }

                const aiHtml = `
                    <div class="bg-gradient-to-r from-purple-50 to-blue-50 p-4 rounded-lg border-2 ${stateInfo.border} mb-4 shadow-sm">
                        <div class="flex justify-between items-center mb-1">
                            <span class="font-bold text-purple-700 text-sm">🧠 AI 预测</span>
                            <span class="text-xs font-medium text-gray-500">更新: 每30分钟</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-lg font-bold ${stateInfo.color}">${stateInfo.label}</span>
                            <span class="text-sm font-medium text-gray-600">置信度: ${confidence}%</span>
                        </div>
                        <div class="w-full bg-gray-200 rounded-full h-2 mt-1">
                            <div class="bg-purple-600 h-2 rounded-full transition-all duration-500" style="width: ${Math.min(100, confidence)}%"></div>
                        </div>
                        ${probaHtml}
                        ${analysis.current_ai_state !== undefined ? `
                            <div class="text-xs text-gray-400 mt-1">状态码: ${analysis.current_ai_state} | 策略: ${analysis.strategy_name || 'N/A'}</div>
                        ` : ''}
                    </div>
                `;
                analysisContainer.innerHTML += aiHtml;
            } else {
                // 显示等待 AI 预测的提示
                analysisContainer.innerHTML += `
                    <div class="bg-gray-50 p-3 rounded-lg border border-gray-200 mb-3 text-center text-sm text-gray-500">
                        ⏳ AI 预测等待中... (首次预测需运行30分钟)
                    </div>
                `;
            }

            // ====== 2. 原有策略分析数据 ======
            const specialKeys = ['signal', 'price', 'explanation', 'ai_state', 'ai_confidence', 'ai_probabilities', 'current_ai_state', 'strategy_name', 'bot_name'];
            let hasOtherData = false;
            Object.entries(analysis).forEach(([key, value]) => {
                if (!specialKeys.includes(key) && value !== null && value !== undefined) {
                    hasOtherData = true;
                    let formattedValue = typeof value === 'number' ? value.toFixed(4) : String(value);
                    const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                    analysisContainer.innerHTML += `<div class="flex justify-between py-1 border-b border-gray-50"><span class="text-gray-500 text-xs">${label}</span><span class="font-semibold text-gray-800 text-xs">${formattedValue}</span></div>`;
                }
            });

            // ====== 3. 解释信息 ======
            if (analysis.explanation) {
                analysisContainer.innerHTML += `<div class="mt-2 text-xs text-gray-500 italic bg-gray-50 p-2 rounded">${analysis.explanation}</div>`;
            }

            // 如果没有其他数据，显示提示
            if (!hasOtherData && !analysis.explanation) {
                analysisContainer.innerHTML += `<div class="text-center text-gray-400 text-xs py-2">暂无额外分析数据</div>`;
            }

        } catch (e) {
            console.error('Error fetching analysis:', e);
            analysisSignal.textContent = 'ERROR';
            analysisSignal.className = `mt-4 text-center font-bold text-lg p-2 rounded-md bg-red-200 text-red-900`;
            analysisContainer.innerHTML = `<p class="text-center text-red-500 text-sm">${e.message}</p>`;
        }
    }

    // --- Pusat Kontrol ---
    async function initializePage() {
        await fetchBotDetails();
        const analysisInterval = botData && botData.status === 'Aktif' ? 5000 : 30000;
        fetchBotHistory();
        fetchAndDisplayAnalysis();
        setInterval(fetchAndDisplayAnalysis, analysisInterval);
        setInterval(fetchBotHistory, 10000);
    }

    initializePage();
});