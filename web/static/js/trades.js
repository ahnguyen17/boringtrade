// BoringTrade Trades JavaScript

// DOM elements
const activeTradesTableBody = document.getElementById('active-trades-table-body');
const completedTradesTableBody = document.getElementById('completed-trades-table-body');
const totalTradesCount = document.getElementById('total-trades-count');
const winRate = document.getElementById('win-rate');
const profitFactor = document.getElementById('profit-factor');
const averageRR = document.getElementById('average-rr');
const exportTradesBtn = document.getElementById('export-trades-btn');

// Initialize trades page
document.addEventListener('DOMContentLoaded', () => {
    // Fetch trades
    fetchTrades();
    
    // Set up event listeners
    setupTradesEventListeners();
    
    // Set up WebSocket event listeners
    setupTradesWebSocketListeners();
});

// Set up event listeners
function setupTradesEventListeners() {
    // Export trades button
    exportTradesBtn.addEventListener('click', exportTrades);
}

// Set up WebSocket event listeners
function setupTradesWebSocketListeners() {
    // Trade update event
    socket.on('trade_update', (trade) => {
        // Refresh trades
        fetchTrades();
    });
}

// Fetch trades
function fetchTrades() {
    fetch('/api/trades')
        .then(response => response.json())
        .then(data => {
            updateTradesUI(data);
            updateTradeStatistics(data);
        })
        .catch(error => {
            console.error('Error fetching trades:', error);
        });
}

// Update trades UI
function updateTradesUI(data) {
    const activeTrades = data.active_trades || [];
    const completedTrades = data.completed_trades || [];
    
    // Update active trades table
    if (activeTrades.length === 0) {
        activeTradesTableBody.innerHTML = '<tr><td colspan="10" class="text-center">No active trades</td></tr>';
    } else {
        activeTradesTableBody.innerHTML = '';
        
        activeTrades.forEach(trade => {
            const row = document.createElement('tr');
            
            // Format entry time
            const entryTime = trade.entry_time ? new Date(trade.entry_time).toLocaleString() : 'Pending';
            
            // Format direction with color
            const direction = trade.direction;
            const directionClass = direction === 'LONG' ? 'text-success' : 'text-danger';
            
            // Calculate current P/L
            let pl = 'N/A';
            if (trade.entry_price && trade.current_price) {
                if (direction === 'LONG') {
                    pl = (trade.current_price - trade.entry_price) * trade.quantity;
                } else {
                    pl = (trade.entry_price - trade.current_price) * trade.quantity;
                }
                pl = pl.toFixed(2);
            }
            
            row.innerHTML = `
                <td>${trade.id}</td>
                <td>${trade.symbol}</td>
                <td class="${directionClass}">${direction}</td>
                <td>${entryTime}</td>
                <td>${trade.entry_price ? trade.entry_price.toFixed(2) : 'Pending'}</td>
                <td>${trade.quantity}</td>
                <td>${trade.stop_loss ? trade.stop_loss.toFixed(2) : 'N/A'}</td>
                <td>${trade.take_profit ? trade.take_profit.toFixed(2) : 'N/A'}</td>
                <td>${pl}</td>
                <td>
                    <button class="btn btn-sm btn-danger close-trade-btn" data-trade-id="${trade.id}">Close</button>
                    <button class="btn btn-sm btn-warning modify-trade-btn" data-trade-id="${trade.id}">Modify</button>
                </td>
            `;
            
            activeTradesTableBody.appendChild(row);
        });
        
        // Add event listeners to close and modify buttons
        document.querySelectorAll('.close-trade-btn').forEach(button => {
            button.addEventListener('click', () => {
                const tradeId = button.getAttribute('data-trade-id');
                closeTrade(tradeId);
            });
        });
        
        document.querySelectorAll('.modify-trade-btn').forEach(button => {
            button.addEventListener('click', () => {
                const tradeId = button.getAttribute('data-trade-id');
                showModifyTradeModal(tradeId);
            });
        });
    }
    
    // Update completed trades table
    if (completedTrades.length === 0) {
        completedTradesTableBody.innerHTML = '<tr><td colspan="11" class="text-center">No completed trades</td></tr>';
    } else {
        completedTradesTableBody.innerHTML = '';
        
        completedTrades.forEach(trade => {
            const row = document.createElement('tr');
            
            // Format times
            const entryTime = trade.entry_time ? new Date(trade.entry_time).toLocaleString() : 'N/A';
            const exitTime = trade.exit_time ? new Date(trade.exit_time).toLocaleString() : 'N/A';
            
            // Format direction with color
            const direction = trade.direction;
            const directionClass = direction === 'LONG' ? 'text-success' : 'text-danger';
            
            // Format result with color
            const result = trade.result;
            let resultClass = 'text-secondary';
            if (result === 'WIN') {
                resultClass = 'text-success';
            } else if (result === 'LOSS') {
                resultClass = 'text-danger';
            }
            
            // Calculate P/L
            let pl = 'N/A';
            if (trade.entry_price && trade.exit_price) {
                if (direction === 'LONG') {
                    pl = (trade.exit_price - trade.entry_price) * trade.quantity;
                } else {
                    pl = (trade.entry_price - trade.exit_price) * trade.quantity;
                }
                pl = pl.toFixed(2);
            }
            
            row.innerHTML = `
                <td>${trade.id}</td>
                <td>${trade.symbol}</td>
                <td class="${directionClass}">${direction}</td>
                <td>${entryTime}</td>
                <td>${exitTime}</td>
                <td>${trade.entry_price ? trade.entry_price.toFixed(2) : 'N/A'}</td>
                <td>${trade.exit_price ? trade.exit_price.toFixed(2) : 'N/A'}</td>
                <td>${trade.quantity}</td>
                <td>${pl}</td>
                <td class="${resultClass}">${result}</td>
                <td>${trade.strategy}</td>
            `;
            
            completedTradesTableBody.appendChild(row);
        });
    }
}

// Update trade statistics
function updateTradeStatistics(data) {
    const completedTrades = data.completed_trades || [];
    
    // Total trades
    totalTradesCount.textContent = completedTrades.length;
    
    if (completedTrades.length === 0) {
        winRate.textContent = '0%';
        profitFactor.textContent = '0.00';
        averageRR.textContent = '0.00';
        return;
    }
    
    // Win rate
    const wins = completedTrades.filter(trade => trade.result === 'WIN').length;
    const winRateValue = (wins / completedTrades.length) * 100;
    winRate.textContent = `${winRateValue.toFixed(1)}%`;
    
    // Profit factor and average R:R
    let totalProfit = 0;
    let totalLoss = 0;
    let totalRR = 0;
    
    completedTrades.forEach(trade => {
        if (trade.entry_price && trade.exit_price) {
            let pl = 0;
            if (trade.direction === 'LONG') {
                pl = (trade.exit_price - trade.entry_price) * trade.quantity;
            } else {
                pl = (trade.entry_price - trade.exit_price) * trade.quantity;
            }
            
            if (pl > 0) {
                totalProfit += pl;
            } else {
                totalLoss += Math.abs(pl);
            }
            
            // Calculate R:R if stop loss is available
            if (trade.stop_loss) {
                let risk = 0;
                if (trade.direction === 'LONG') {
                    risk = (trade.entry_price - trade.stop_loss) * trade.quantity;
                } else {
                    risk = (trade.stop_loss - trade.entry_price) * trade.quantity;
                }
                
                if (risk > 0) {
                    const rr = Math.abs(pl) / risk;
                    totalRR += rr;
                }
            }
        }
    });
    
    // Calculate profit factor
    const profitFactorValue = totalLoss > 0 ? totalProfit / totalLoss : totalProfit;
    profitFactor.textContent = profitFactorValue.toFixed(2);
    
    // Calculate average R:R
    const averageRRValue = totalRR / completedTrades.length;
    averageRR.textContent = averageRRValue.toFixed(2);
}

// Close trade
function closeTrade(tradeId) {
    if (confirm('Are you sure you want to close this trade?')) {
        fetch(`/api/trades/${tradeId}/close`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('success', 'Trade closed successfully');
                fetchTrades();
            } else {
                showAlert('danger', `Failed to close trade: ${data.message || data.error}`);
            }
        })
        .catch(error => {
            console.error('Error closing trade:', error);
            showAlert('danger', 'Error closing trade');
        });
    }
}

// Export trades to CSV
function exportTrades() {
    fetch('/api/trades')
        .then(response => response.json())
        .then(data => {
            const completedTrades = data.completed_trades || [];
            
            if (completedTrades.length === 0) {
                showAlert('warning', 'No completed trades to export');
                return;
            }
            
            // Create CSV content
            let csv = 'ID,Symbol,Direction,Entry Time,Exit Time,Entry Price,Exit Price,Quantity,P/L,Result,Strategy\n';
            
            completedTrades.forEach(trade => {
                const entryTime = trade.entry_time ? new Date(trade.entry_time).toLocaleString() : '';
                const exitTime = trade.exit_time ? new Date(trade.exit_time).toLocaleString() : '';
                
                let pl = '';
                if (trade.entry_price && trade.exit_price) {
                    if (trade.direction === 'LONG') {
                        pl = (trade.exit_price - trade.entry_price) * trade.quantity;
                    } else {
                        pl = (trade.entry_price - trade.exit_price) * trade.quantity;
                    }
                    pl = pl.toFixed(2);
                }
                
                csv += `${trade.id},${trade.symbol},${trade.direction},"${entryTime}","${exitTime}",${trade.entry_price || ''},${trade.exit_price || ''},${trade.quantity},${pl},${trade.result},${trade.strategy}\n`;
            });
            
            // Create download link
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.setAttribute('hidden', '');
            a.setAttribute('href', url);
            a.setAttribute('download', `boringtrade_trades_${new Date().toISOString().slice(0, 10)}.csv`);
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        })
        .catch(error => {
            console.error('Error exporting trades:', error);
            showAlert('danger', 'Error exporting trades');
        });
}
