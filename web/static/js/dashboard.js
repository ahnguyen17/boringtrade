// BoringTrade Dashboard JavaScript

// Connect to WebSocket
const socket = io();

// DOM elements
const botStatusBadge = document.getElementById('bot-status-badge');
const startBotBtn = document.getElementById('start-bot-btn');
const stopBotBtn = document.getElementById('stop-bot-btn');
const flattenAllBtn = document.getElementById('flatten-all-btn');
const activeTradesContainer = document.getElementById('active-trades-container');
const keyLevelsContainer = document.getElementById('key-levels-container');
const notificationsContainer = document.getElementById('notifications-container');

// Initialize dashboard
function initDashboard() {
    // Get bot status
    fetchBotStatus();
    
    // Get active trades
    fetchTrades();
    
    // Get key levels
    fetchLevels();
    
    // Get notifications
    fetchNotifications();
    
    // Set up event listeners
    setupEventListeners();
    
    // Set up WebSocket event listeners
    setupWebSocketListeners();
}

// Fetch bot status
function fetchBotStatus() {
    fetch('/api/bot/status')
        .then(response => response.json())
        .then(data => {
            updateBotStatus(data.status);
        })
        .catch(error => {
            console.error('Error fetching bot status:', error);
            updateBotStatus('error');
        });
}

// Update bot status UI
function updateBotStatus(status) {
    let badgeClass = 'bg-secondary';
    let statusText = 'Unknown';
    
    switch (status) {
        case 'running':
            badgeClass = 'bg-success';
            statusText = 'Running';
            break;
        case 'stopped':
            badgeClass = 'bg-danger';
            statusText = 'Stopped';
            break;
        case 'not_initialized':
            badgeClass = 'bg-warning';
            statusText = 'Not Initialized';
            break;
        case 'error':
            badgeClass = 'bg-danger';
            statusText = 'Error';
            break;
    }
    
    botStatusBadge.className = `badge ${badgeClass}`;
    botStatusBadge.textContent = statusText;
    
    // Update button states
    startBotBtn.disabled = status === 'running';
    stopBotBtn.disabled = status !== 'running';
    flattenAllBtn.disabled = status !== 'running';
}

// Fetch trades
function fetchTrades() {
    fetch('/api/trades')
        .then(response => response.json())
        .then(data => {
            updateTradesUI(data);
        })
        .catch(error => {
            console.error('Error fetching trades:', error);
        });
}

// Update trades UI
function updateTradesUI(data) {
    const activeTrades = data.active_trades || [];
    
    if (activeTrades.length === 0) {
        activeTradesContainer.innerHTML = '<p>No active trades</p>';
        return;
    }
    
    let html = '<div class="table-responsive"><table class="table table-sm table-striped">';
    html += '<thead><tr><th>Symbol</th><th>Direction</th><th>Entry</th><th>Stop</th><th>Target</th><th>P/L</th></tr></thead>';
    html += '<tbody>';
    
    activeTrades.forEach(trade => {
        const direction = trade.direction;
        const directionClass = direction === 'LONG' ? 'text-success' : 'text-danger';
        
        let pl = 'N/A';
        if (trade.entry_price && trade.symbol) {
            // In a real implementation, we would get the current price from the data feed
            // For now, we'll just use the entry price
            const currentPrice = trade.entry_price;
            if (direction === 'LONG') {
                pl = (currentPrice - trade.entry_price) * trade.quantity;
            } else {
                pl = (trade.entry_price - currentPrice) * trade.quantity;
            }
            pl = pl.toFixed(2);
        }
        
        html += `<tr>
            <td>${trade.symbol}</td>
            <td class="${directionClass}">${direction}</td>
            <td>${trade.entry_price ? trade.entry_price.toFixed(2) : 'N/A'}</td>
            <td>${trade.stop_loss ? trade.stop_loss.toFixed(2) : 'N/A'}</td>
            <td>${trade.take_profit ? trade.take_profit.toFixed(2) : 'N/A'}</td>
            <td>${pl}</td>
        </tr>`;
    });
    
    html += '</tbody></table></div>';
    activeTradesContainer.innerHTML = html;
}

// Fetch levels
function fetchLevels() {
    fetch('/api/levels')
        .then(response => response.json())
        .then(data => {
            updateLevelsUI(data);
        })
        .catch(error => {
            console.error('Error fetching levels:', error);
        });
}

// Update levels UI
function updateLevelsUI(levels) {
    if (levels.length === 0) {
        keyLevelsContainer.innerHTML = '<p>No key levels</p>';
        return;
    }
    
    let html = '<div class="table-responsive"><table class="table table-sm table-striped">';
    html += '<thead><tr><th>Symbol</th><th>Type</th><th>Price</th><th>Broken</th><th>Retested</th></tr></thead>';
    html += '<tbody>';
    
    levels.forEach(level => {
        const broken = level.has_been_broken ? 'Yes' : 'No';
        const retested = level.has_been_retested ? 'Yes' : 'No';
        
        html += `<tr>
            <td>${level.symbol}</td>
            <td>${level.level_type}</td>
            <td>${level.price.toFixed(2)}</td>
            <td>${broken}</td>
            <td>${retested}</td>
        </tr>`;
    });
    
    html += '</tbody></table></div>';
    keyLevelsContainer.innerHTML = html;
}

// Fetch notifications
function fetchNotifications() {
    fetch('/api/notifications')
        .then(response => response.json())
        .then(data => {
            updateNotificationsUI(data);
        })
        .catch(error => {
            console.error('Error fetching notifications:', error);
        });
}

// Update notifications UI
function updateNotificationsUI(notifications) {
    if (notifications.length === 0) {
        notificationsContainer.innerHTML = '<p>No notifications</p>';
        return;
    }
    
    let html = '<div class="list-group">';
    
    // Show only the last 10 notifications
    const recentNotifications = notifications.slice(0, 10);
    
    recentNotifications.forEach(notification => {
        const timestamp = new Date(notification.timestamp).toLocaleString();
        const typeClass = getNotificationTypeClass(notification.type);
        
        html += `<div class="list-group-item list-group-item-${typeClass}">
            <div class="d-flex w-100 justify-content-between">
                <h5 class="mb-1">${notification.title}</h5>
                <small>${timestamp}</small>
            </div>
            <p class="mb-1">${notification.message}</p>
        </div>`;
    });
    
    html += '</div>';
    notificationsContainer.innerHTML = html;
}

// Get notification type class
function getNotificationTypeClass(type) {
    switch (type) {
        case 'info':
            return 'info';
        case 'warning':
            return 'warning';
        case 'error':
            return 'danger';
        case 'trade':
            return 'success';
        case 'summary':
            return 'primary';
        default:
            return 'light';
    }
}

// Set up event listeners
function setupEventListeners() {
    // Start bot button
    startBotBtn.addEventListener('click', () => {
        fetch('/api/bot/start', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateBotStatus('running');
                    showAlert('success', 'Bot started successfully');
                } else {
                    showAlert('danger', `Failed to start bot: ${data.message || data.error}`);
                }
            })
            .catch(error => {
                console.error('Error starting bot:', error);
                showAlert('danger', 'Error starting bot');
            });
    });
    
    // Stop bot button
    stopBotBtn.addEventListener('click', () => {
        fetch('/api/bot/stop', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateBotStatus('stopped');
                    showAlert('success', 'Bot stopped successfully');
                } else {
                    showAlert('danger', `Failed to stop bot: ${data.message || data.error}`);
                }
            })
            .catch(error => {
                console.error('Error stopping bot:', error);
                showAlert('danger', 'Error stopping bot');
            });
    });
    
    // Flatten all button
    flattenAllBtn.addEventListener('click', () => {
        if (confirm('Are you sure you want to flatten all positions?')) {
            fetch('/api/bot/flatten', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showAlert('success', 'All positions flattened');
                        fetchTrades();
                    } else {
                        showAlert('danger', `Failed to flatten positions: ${data.message || data.error}`);
                    }
                })
                .catch(error => {
                    console.error('Error flattening positions:', error);
                    showAlert('danger', 'Error flattening positions');
                });
        }
    });
}

// Set up WebSocket event listeners
function setupWebSocketListeners() {
    // Connection events
    socket.on('connect', () => {
        console.log('Connected to server');
    });
    
    socket.on('disconnect', () => {
        console.log('Disconnected from server');
    });
    
    // Notification event
    socket.on('notification', (notification) => {
        // Add notification to UI
        addNotification(notification);
    });
    
    // Trade update event
    socket.on('trade_update', (trade) => {
        // Refresh trades
        fetchTrades();
    });
    
    // Level update event
    socket.on('level_update', (level) => {
        // Refresh levels
        fetchLevels();
    });
}

// Add notification to UI
function addNotification(notification) {
    // Get existing notifications
    fetch('/api/notifications')
        .then(response => response.json())
        .then(data => {
            updateNotificationsUI(data);
        })
        .catch(error => {
            console.error('Error fetching notifications:', error);
        });
}

// Show alert
function showAlert(type, message) {
    const alertContainer = document.createElement('div');
    alertContainer.className = `alert alert-${type} alert-dismissible fade show`;
    alertContainer.setAttribute('role', 'alert');
    alertContainer.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add alert to the top of the page
    const container = document.querySelector('.container');
    container.insertBefore(alertContainer, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertContainer.remove();
    }, 5000);
}

// Initialize dashboard when the page loads
document.addEventListener('DOMContentLoaded', initDashboard);
