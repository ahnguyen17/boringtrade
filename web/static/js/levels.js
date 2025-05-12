// BoringTrade Levels JavaScript

// Register Chart.js plugins
// The plugins are now auto-registered with Chart.js 4.x

// DOM elements
const symbolFilter = document.getElementById('symbol-filter');
const levelTypeFilter = document.getElementById('level-type-filter');
const levelsTableBody = document.getElementById('levels-table-body');
const refreshLevelsBtn = document.getElementById('refresh-levels-btn');
const addManualLevelBtn = document.getElementById('add-manual-level-btn');
const saveLevelBtn = document.getElementById('save-level-btn');
const levelSymbol = document.getElementById('level-symbol');
const levelPrice = document.getElementById('level-price');
const levelDescription = document.getElementById('level-description');
const chartSymbol = document.getElementById('chart-symbol');
const chartTimeframe = document.getElementById('chart-timeframe');
const loadChartBtn = document.getElementById('load-chart-btn');
const chartContainer = document.getElementById('chart-container');

// Chart instance
let priceChart = null;

// Initialize levels page
document.addEventListener('DOMContentLoaded', () => {
    // Fetch levels
    fetchLevels();

    // Fetch symbols for dropdowns
    fetchSymbols();

    // Set up event listeners
    setupLevelsEventListeners();

    // Set up WebSocket event listeners
    setupLevelsWebSocketListeners();
});

// Set up event listeners
function setupLevelsEventListeners() {
    // Refresh levels button
    refreshLevelsBtn.addEventListener('click', fetchLevels);

    // Symbol filter
    symbolFilter.addEventListener('change', filterLevels);

    // Level type filter
    levelTypeFilter.addEventListener('change', filterLevels);

    // Save level button
    saveLevelBtn.addEventListener('click', saveManualLevel);

    // Load chart button
    loadChartBtn.addEventListener('click', loadChart);
}

// Set up WebSocket event listeners
function setupLevelsWebSocketListeners() {
    // Level update event
    socket.on('level_update', (level) => {
        // Refresh levels
        fetchLevels();
    });
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

// Fetch symbols
function fetchSymbols() {
    fetch('/api/symbols')
        .then(response => response.json())
        .then(data => {
            updateSymbolDropdowns(data);
        })
        .catch(error => {
            console.error('Error fetching symbols:', error);
        });
}

// Update symbol dropdowns
function updateSymbolDropdowns(symbols) {
    // Clear existing options except the first one
    while (symbolFilter.options.length > 1) {
        symbolFilter.remove(1);
    }

    while (levelSymbol.options.length > 1) {
        levelSymbol.remove(1);
    }

    while (chartSymbol.options.length > 1) {
        chartSymbol.remove(1);
    }

    // Add symbols to dropdowns
    symbols.forEach(symbol => {
        // Symbol filter
        const filterOption = document.createElement('option');
        filterOption.value = symbol;
        filterOption.textContent = symbol;
        symbolFilter.appendChild(filterOption);

        // Level symbol
        const levelOption = document.createElement('option');
        levelOption.value = symbol;
        levelOption.textContent = symbol;
        levelSymbol.appendChild(levelOption);

        // Chart symbol
        const chartOption = document.createElement('option');
        chartOption.value = symbol;
        chartOption.textContent = symbol;
        chartSymbol.appendChild(chartOption);
    });
}

// Update levels UI
function updateLevelsUI(levels) {
    if (levels.length === 0) {
        levelsTableBody.innerHTML = '<tr><td colspan="7" class="text-center">No price levels found</td></tr>';
        return;
    }

    // Apply filters
    const filteredLevels = filterLevelsData(levels);

    if (filteredLevels.length === 0) {
        levelsTableBody.innerHTML = '<tr><td colspan="7" class="text-center">No price levels match the current filters</td></tr>';
        return;
    }

    levelsTableBody.innerHTML = '';

    filteredLevels.forEach(level => {
        const row = document.createElement('tr');

        // Format created time
        const createdAt = level.created_at ? new Date(level.created_at).toLocaleString() : 'N/A';

        // Format status
        let statusBadge = '';
        if (level.has_been_broken && level.has_been_retested) {
            statusBadge = '<span class="badge bg-success">Broken & Retested</span>';
        } else if (level.has_been_broken) {
            statusBadge = '<span class="badge bg-warning">Broken</span>';
        } else {
            statusBadge = '<span class="badge bg-secondary">Active</span>';
        }

        row.innerHTML = `
            <td>${level.symbol}</td>
            <td>${level.level_type}</td>
            <td>${level.price.toFixed(2)}</td>
            <td>${createdAt}</td>
            <td>${statusBadge}</td>
            <td>${level.description || ''}</td>
            <td>
                <button class="btn btn-sm btn-danger delete-level-btn" data-level-id="${level.id}">Delete</button>
            </td>
        `;

        levelsTableBody.appendChild(row);
    });

    // Add event listeners to delete buttons
    document.querySelectorAll('.delete-level-btn').forEach(button => {
        button.addEventListener('click', () => {
            const levelId = button.getAttribute('data-level-id');
            deleteLevel(levelId);
        });
    });
}

// Filter levels data
function filterLevelsData(levels) {
    const symbolValue = symbolFilter.value;
    const typeValue = levelTypeFilter.value;

    return levels.filter(level => {
        // Apply symbol filter
        if (symbolValue !== 'all' && level.symbol !== symbolValue) {
            return false;
        }

        // Apply type filter
        if (typeValue !== 'all' && level.level_type !== typeValue) {
            return false;
        }

        return true;
    });
}

// Filter levels based on UI filters
function filterLevels() {
    fetchLevels();
}

// Save manual level
function saveManualLevel() {
    const symbol = levelSymbol.value;
    const price = parseFloat(levelPrice.value);
    const description = levelDescription.value;

    if (!symbol) {
        showAlert('warning', 'Please select a symbol');
        return;
    }

    if (isNaN(price) || price <= 0) {
        showAlert('warning', 'Please enter a valid price');
        return;
    }

    const levelData = {
        symbol,
        price,
        level_type: 'MANUAL',
        description
    };

    fetch('/api/levels', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(levelData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'Manual level added successfully');
            fetchLevels();

            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('add-level-modal'));
            modal.hide();

            // Reset form
            levelSymbol.value = '';
            levelPrice.value = '';
            levelDescription.value = '';
        } else {
            showAlert('danger', `Failed to add manual level: ${data.message || data.error}`);
        }
    })
    .catch(error => {
        console.error('Error adding manual level:', error);
        showAlert('danger', 'Error adding manual level');
    });
}

// Delete level
function deleteLevel(levelId) {
    if (confirm('Are you sure you want to delete this level?')) {
        fetch(`/api/levels/${levelId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('success', 'Level deleted successfully');
                fetchLevels();
            } else {
                showAlert('danger', `Failed to delete level: ${data.message || data.error}`);
            }
        })
        .catch(error => {
            console.error('Error deleting level:', error);
            showAlert('danger', 'Error deleting level');
        });
    }
}

// Load chart
function loadChart() {
    const symbol = chartSymbol.value;
    const timeframe = chartTimeframe.value;

    if (!symbol) {
        showAlert('warning', 'Please select a symbol');
        return;
    }

    // Show loading message
    chartContainer.innerHTML = '<div class="d-flex justify-content-center align-items-center h-100"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';

    // Fetch candles
    fetch(`/api/candles?symbol=${symbol}&timeframe=${timeframe}`)
        .then(response => response.json())
        .then(data => {
            renderChart(symbol, timeframe, data);
        })
        .catch(error => {
            console.error('Error loading chart:', error);
            chartContainer.innerHTML = '<div class="d-flex justify-content-center align-items-center h-100"><p class="text-danger">Error loading chart</p></div>';
        });
}

// Render chart
function renderChart(symbol, timeframe, candles) {
    // Destroy existing chart if any
    if (priceChart) {
        priceChart.destroy();
    }

    // Prepare chart container
    chartContainer.innerHTML = '<canvas id="price-chart"></canvas>';

    // Prepare data for candlestick chart
    const data = candles.map(candle => ({
        x: new Date(candle.timestamp),
        o: candle.open_price,
        h: candle.high_price,
        l: candle.low_price,
        c: candle.close_price
    }));

    // Create chart
    const ctx = document.getElementById('price-chart').getContext('2d');

    // Create a proper candlestick chart using chartjs-chart-financial
    priceChart = new Chart(ctx, {
        type: 'candlestick',
        data: {
            datasets: [{
                label: `${symbol} (${timeframe}m)`,
                data: data,
                color: {
                    up: 'rgba(38, 166, 154, 1)',
                    down: 'rgba(239, 83, 80, 1)',
                    unchanged: 'rgba(100, 100, 100, 1)',
                },
                borderColor: {
                    up: 'rgba(38, 166, 154, 1)',
                    down: 'rgba(239, 83, 80, 1)',
                    unchanged: 'rgba(100, 100, 100, 1)',
                },
                backgroundColor: {
                    up: 'rgba(38, 166, 154, 0.5)',
                    down: 'rgba(239, 83, 80, 0.5)',
                    unchanged: 'rgba(100, 100, 100, 0.5)',
                }
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: timeframe >= 60 ? 'day' : 'hour',
                        displayFormats: {
                            hour: 'MMM d, HH:mm',
                            day: 'MMM d'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Price'
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const point = context.raw;
                            return [
                                `Open: ${point.o.toFixed(2)}`,
                                `High: ${point.h.toFixed(2)}`,
                                `Low: ${point.l.toFixed(2)}`,
                                `Close: ${point.c.toFixed(2)}`
                            ];
                        }
                    }
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            }
        }
    });

    // Add price levels to the chart
    addLevelsToChart(symbol);
}

// Add price levels to the chart
function addLevelsToChart(symbol) {
    // Fetch levels for the symbol
    fetch('/api/levels')
        .then(response => response.json())
        .then(levels => {
            // Filter levels for the current symbol
            const symbolLevels = levels.filter(level => level.symbol === symbol);

            if (symbolLevels.length === 0) {
                return;
            }

            // Add horizontal lines for each level
            const levelColors = {
                'ORH': 'rgba(255, 193, 7, 1)',  // Warning yellow
                'ORL': 'rgba(255, 193, 7, 1)',  // Warning yellow
                'PDH': 'rgba(13, 110, 253, 1)', // Primary blue
                'PDL': 'rgba(13, 110, 253, 1)', // Primary blue
                'OB_BULLISH': 'rgba(25, 135, 84, 1)', // Success green
                'OB_BEARISH': 'rgba(220, 53, 69, 1)', // Danger red
                'MANUAL': 'rgba(108, 117, 125, 1)' // Secondary gray
            };

            // Create annotations for each level
            const annotations = {};

            symbolLevels.forEach((level, index) => {
                const color = levelColors[level.level_type] || 'rgba(108, 117, 125, 1)';
                const labelText = `${level.level_type} (${level.price.toFixed(2)})`;

                annotations[`level-${index}`] = {
                    type: 'line',
                    yMin: level.price,
                    yMax: level.price,
                    borderColor: color,
                    borderWidth: 2,
                    borderDash: [5, 5],
                    label: {
                        display: true,
                        content: labelText,
                        backgroundColor: color,
                        color: 'white',
                        font: {
                            size: 10
                        },
                        position: 'start'
                    }
                };
            });

            // Add annotations to chart
            priceChart.options.plugins.annotation = {
                annotations: annotations
            };

            // Update chart
            priceChart.update();
        })
        .catch(error => {
            console.error('Error fetching levels for chart:', error);
        });
}
