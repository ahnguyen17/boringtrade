// BoringTrade Trading JavaScript

// Connect to WebSocket
const socket = io();

// DOM elements
const symbolSelect = document.getElementById('symbol');
const directionLongRadio = document.getElementById('direction-long');
const directionShortRadio = document.getElementById('direction-short');
const quantityInput = document.getElementById('quantity');
const entryPriceInput = document.getElementById('entry-price');
const stopLossInput = document.getElementById('stop-loss');
const takeProfitInput = document.getElementById('take-profit');
const riskAmountElement = document.getElementById('risk-amount');
const riskRewardElement = document.getElementById('risk-reward');
const refreshPriceBtn = document.getElementById('refresh-price-btn');
const placeOrderBtn = document.getElementById('place-order-btn');
const orderForm = document.getElementById('order-form');
const activePositionsContainer = document.getElementById('active-positions-container');
const orderStatusContainer = document.getElementById('order-status-container');

// Initialize trading page
document.addEventListener('DOMContentLoaded', () => {
    // Fetch symbols
    fetchSymbols();
    
    // Set up event listeners
    setupEventListeners();
    
    // Set up WebSocket event listeners
    setupWebSocketListeners();
});

// Set up event listeners
function setupEventListeners() {
    // Symbol change
    symbolSelect.addEventListener('change', () => {
        fetchCurrentPrice();
    });
    
    // Direction change
    directionLongRadio.addEventListener('change', updateRiskAnalysis);
    directionShortRadio.addEventListener('change', updateRiskAnalysis);
    
    // Input changes
    quantityInput.addEventListener('input', updateRiskAnalysis);
    stopLossInput.addEventListener('input', updateRiskAnalysis);
    takeProfitInput.addEventListener('input', updateRiskAnalysis);
    
    // Refresh price button
    refreshPriceBtn.addEventListener('click', fetchCurrentPrice);
    
    // Order form submission
    orderForm.addEventListener('submit', (event) => {
        event.preventDefault();
        placeOrder();
    });
}

// Set up WebSocket event listeners
function setupWebSocketListeners() {
    // Trade update event
    socket.on('trade_update', (trade) => {
        // Refresh positions
        fetchPositions();
    });
    
    // Order update event
    socket.on('order_update', (order) => {
        // Add order to status container
        addOrderStatus(order);
    });
}

// Fetch symbols
function fetchSymbols() {
    fetch('/api/symbols')
        .then(response => response.json())
        .then(data => {
            updateSymbolsDropdown(data);
        })
        .catch(error => {
            console.error('Error fetching symbols:', error);
            showAlert('danger', 'Failed to fetch symbols');
        });
}

// Update symbols dropdown
function updateSymbolsDropdown(symbols) {
    // Clear existing options
    symbolSelect.innerHTML = '<option value="" selected disabled>Select a symbol</option>';
    
    // Add symbols
    symbols.forEach(symbol => {
        const option = document.createElement('option');
        option.value = symbol;
        option.textContent = symbol;
        symbolSelect.appendChild(option);
    });
    
    // Trigger change event to fetch price
    if (symbols.length > 0) {
        symbolSelect.value = symbols[0];
        fetchCurrentPrice();
    }
}

// Fetch current price
function fetchCurrentPrice() {
    const symbol = symbolSelect.value;
    
    if (!symbol) {
        return;
    }
    
    // Show loading state
    entryPriceInput.value = 'Loading...';
    
    // Fetch latest candle
    fetch(`/api/candles?symbol=${symbol}&timeframe=1`)
        .then(response => response.json())
        .then(data => {
            if (data && data.length > 0) {
                // Get latest candle
                const latestCandle = data[0];
                
                // Update entry price
                entryPriceInput.value = latestCandle.close_price.toFixed(2);
                
                // Set default stop loss and take profit
                if (!stopLossInput.value) {
                    if (directionLongRadio.checked) {
                        stopLossInput.value = (latestCandle.close_price * 0.99).toFixed(2);
                    } else {
                        stopLossInput.value = (latestCandle.close_price * 1.01).toFixed(2);
                    }
                }
                
                if (!takeProfitInput.value) {
                    if (directionLongRadio.checked) {
                        takeProfitInput.value = (latestCandle.close_price * 1.02).toFixed(2);
                    } else {
                        takeProfitInput.value = (latestCandle.close_price * 0.98).toFixed(2);
                    }
                }
                
                // Update risk analysis
                updateRiskAnalysis();
            }
        })
        .catch(error => {
            console.error('Error fetching current price:', error);
            entryPriceInput.value = 'Error';
        });
}

// Update risk analysis
function updateRiskAnalysis() {
    const entryPrice = parseFloat(entryPriceInput.value);
    const stopLoss = parseFloat(stopLossInput.value);
    const takeProfit = parseFloat(takeProfitInput.value);
    const quantity = parseInt(quantityInput.value);
    const isLong = directionLongRadio.checked;
    
    if (isNaN(entryPrice) || isNaN(stopLoss) || isNaN(takeProfit) || isNaN(quantity)) {
        riskAmountElement.textContent = '$0.00';
        riskRewardElement.textContent = '0.00';
        return;
    }
    
    // Calculate risk amount
    let riskAmount;
    if (isLong) {
        riskAmount = (entryPrice - stopLoss) * quantity;
    } else {
        riskAmount = (stopLoss - entryPrice) * quantity;
    }
    
    // Calculate reward amount
    let rewardAmount;
    if (isLong) {
        rewardAmount = (takeProfit - entryPrice) * quantity;
    } else {
        rewardAmount = (entryPrice - takeProfit) * quantity;
    }
    
    // Calculate risk/reward ratio
    const riskReward = rewardAmount / riskAmount;
    
    // Update UI
    riskAmountElement.textContent = `$${riskAmount.toFixed(2)}`;
    riskRewardElement.textContent = riskReward.toFixed(2);
    
    // Highlight based on risk/reward
    if (riskReward >= 2) {
        riskRewardElement.className = 'text-success';
    } else if (riskReward >= 1) {
        riskRewardElement.className = 'text-warning';
    } else {
        riskRewardElement.className = 'text-danger';
    }
}

// Place order
function placeOrder() {
    // Get form values
    const symbol = symbolSelect.value;
    const direction = directionLongRadio.checked ? 'LONG' : 'SHORT';
    const quantity = parseInt(quantityInput.value);
    const entryPrice = parseFloat(entryPriceInput.value);
    const stopLoss = parseFloat(stopLossInput.value);
    const takeProfit = parseFloat(takeProfitInput.value);
    
    // Validate inputs
    if (!symbol || isNaN(quantity) || isNaN(entryPrice) || isNaN(stopLoss) || isNaN(takeProfit)) {
        showAlert('danger', 'Please fill in all fields with valid values');
        return;
    }
    
    // Show loading state
    placeOrderBtn.disabled = true;
    placeOrderBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Placing Order...';
    
    // Send order request
    fetch('/api/trades/place', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            symbol: symbol,
            direction: direction,
            quantity: quantity,
            entry_price: entryPrice,
            stop_loss: stopLoss,
            take_profit: takeProfit
        })
    })
    .then(response => response.json())
    .then(data => {
        // Reset button state
        placeOrderBtn.disabled = false;
        placeOrderBtn.textContent = 'Place Market Order';
        
        if (data.success) {
            // Show success message
            showAlert('success', `Order placed successfully: ${direction} ${quantity} ${symbol}`);
            
            // Add order to status container
            addOrderStatus({
                symbol: symbol,
                direction: direction,
                quantity: quantity,
                status: 'PENDING',
                message: 'Order placed successfully'
            });
            
            // Reset form
            resetOrderForm();
            
            // Fetch positions
            fetchPositions();
        } else {
            // Show error message
            showAlert('danger', `Failed to place order: ${data.message || data.error}`);
            
            // Add order to status container
            addOrderStatus({
                symbol: symbol,
                direction: direction,
                quantity: quantity,
                status: 'ERROR',
                message: data.message || data.error
            });
        }
    })
    .catch(error => {
        console.error('Error placing order:', error);
        
        // Reset button state
        placeOrderBtn.disabled = false;
        placeOrderBtn.textContent = 'Place Market Order';
        
        // Show error message
        showAlert('danger', 'Error placing order');
        
        // Add order to status container
        addOrderStatus({
            symbol: symbol,
            direction: direction,
            quantity: quantity,
            status: 'ERROR',
            message: 'Network error'
        });
    });
}

// Reset order form
function resetOrderForm() {
    // Reset inputs
    quantityInput.value = '1';
    stopLossInput.value = '';
    takeProfitInput.value = '';
    
    // Fetch current price
    fetchCurrentPrice();
}

// Fetch positions
function fetchPositions() {
    fetch('/api/trades')
        .then(response => response.json())
        .then(data => {
            updatePositionsUI(data.active_trades || []);
        })
        .catch(error => {
            console.error('Error fetching positions:', error);
        });
}

// Update positions UI
function updatePositionsUI(positions) {
    if (positions.length === 0) {
        activePositionsContainer.innerHTML = '<p>No active positions</p>';
        return;
    }
    
    let html = '<div class="table-responsive"><table class="position-table table table-sm">';
    html += '<thead><tr><th>Symbol</th><th>Dir</th><th>Qty</th><th>Entry</th><th>P/L</th><th>Actions</th></tr></thead>';
    html += '<tbody>';
    
    positions.forEach(position => {
        const direction = position.direction;
        const directionClass = direction === 'LONG' ? 'position-long' : 'position-short';
        const pl = position.profit_loss_amount ? `$${position.profit_loss_amount.toFixed(2)}` : 'N/A';
        const plClass = position.profit_loss_amount > 0 ? 'text-success' : position.profit_loss_amount < 0 ? 'text-danger' : '';
        
        html += `<tr>
            <td>${position.symbol}</td>
            <td class="${directionClass}">${direction}</td>
            <td>${position.quantity}</td>
            <td>${position.entry_price ? position.entry_price.toFixed(2) : 'N/A'}</td>
            <td class="${plClass}">${pl}</td>
            <td>
                <button class="btn btn-sm btn-danger action-btn" onclick="closePosition('${position.symbol}')">Close</button>
            </td>
        </tr>`;
    });
    
    html += '</tbody></table></div>';
    activePositionsContainer.innerHTML = html;
}

// Close position
function closePosition(symbol) {
    if (confirm(`Are you sure you want to close the ${symbol} position?`)) {
        fetch(`/api/trades/close`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbol: symbol
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('success', `Position closed: ${symbol}`);
                fetchPositions();
            } else {
                showAlert('danger', `Failed to close position: ${data.message || data.error}`);
            }
        })
        .catch(error => {
            console.error('Error closing position:', error);
            showAlert('danger', 'Error closing position');
        });
    }
}

// Add order status
function addOrderStatus(order) {
    // Create status element
    const statusElement = document.createElement('div');
    statusElement.className = 'order-status';
    
    // Set status class
    let statusClass = '';
    if (order.status === 'FILLED') {
        statusClass = 'order-status-success';
    } else if (order.status === 'ERROR') {
        statusClass = 'order-status-error';
    } else {
        statusClass = 'order-status-pending';
    }
    
    // Set status content
    statusElement.innerHTML = `
        <p class="mb-1">
            <strong class="${statusClass}">${order.status}</strong>: 
            ${order.direction} ${order.quantity} ${order.symbol}
        </p>
        <p class="small text-muted mb-0">${order.message || ''}</p>
        <hr>
    `;
    
    // Add to container
    orderStatusContainer.innerHTML = '';
    orderStatusContainer.appendChild(statusElement);
}

// Show alert
function showAlert(type, message) {
    // Create alert element
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${type} alert-dismissible fade show`;
    alertElement.role = 'alert';
    alertElement.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add alert to page
    const container = document.querySelector('.container');
    container.insertBefore(alertElement, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertElement.classList.remove('show');
        setTimeout(() => {
            alertElement.remove();
        }, 150);
    }, 5000);
}
