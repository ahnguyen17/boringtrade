// BoringTrade Configuration JavaScript

// DOM elements
const configForm = document.getElementById('config-form');
const resetConfigBtn = document.getElementById('reset-config-btn');
const testConnectionBtn = document.getElementById('test-connection-btn');
const connectionStatus = document.getElementById('connection-status');
const connectionDetails = document.getElementById('connection-details');
const connectionDetailsText = document.getElementById('connection-details-text');

// Initialize configuration page
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM content loaded');

    // Debug element existence
    console.log('Test connection button exists:', !!testConnectionBtn);
    console.log('Connection status element exists:', !!connectionStatus);
    console.log('Connection details element exists:', !!connectionDetails);
    console.log('Connection details text element exists:', !!connectionDetailsText);

    // Set up event listeners
    setupConfigEventListeners();
});

// Set up event listeners
function setupConfigEventListeners() {
    // Config form submission
    configForm.addEventListener('submit', (event) => {
        event.preventDefault();
        saveConfig();
    });

    // Reset config button
    resetConfigBtn.addEventListener('click', () => {
        if (confirm('Are you sure you want to reset the configuration to default values?')) {
            resetConfig();
        }
    });

    // Test connection button
    if (testConnectionBtn) {
        console.log('Adding event listener to test connection button');
        testConnectionBtn.addEventListener('click', () => {
            console.log('Test connection button clicked');
            testBrokerConnection();
        });
    } else {
        console.error('Test connection button not found');
    }
}

// Save configuration
function saveConfig() {
    // Get form data
    const formData = new FormData(configForm);
    const config = {};

    // Process form data
    for (const [key, value] of formData.entries()) {
        // Handle nested properties (e.g., orb.enabled)
        if (key.includes('.')) {
            const [parent, child] = key.split('.');
            if (!config[parent]) {
                config[parent] = {};
            }
            config[parent][child] = processValue(value);
        } else {
            config[key] = processValue(value);
        }
    }

    // Process assets (comma-separated string to array)
    if (config.assets) {
        config.assets = config.assets.split(',').map(asset => asset.trim()).filter(asset => asset);
    }

    // Send config to server
    fetch('/api/config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'Configuration saved successfully');
        } else {
            showAlert('danger', `Failed to save configuration: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Error saving configuration:', error);
        showAlert('danger', 'Error saving configuration');
    });
}

// Reset configuration to default values
function resetConfig() {
    fetch('/api/config')
        .then(response => response.json())
        .then(data => {
            // Reload the page to show default values
            window.location.reload();
        })
        .catch(error => {
            console.error('Error resetting configuration:', error);
            showAlert('danger', 'Error resetting configuration');
        });
}

// Process form value based on type
function processValue(value) {
    // Convert string to appropriate type
    if (value === 'true') {
        return true;
    } else if (value === 'false') {
        return false;
    } else if (!isNaN(value) && value !== '') {
        return Number(value);
    } else {
        return value;
    }
}

// Test broker connection
function testBrokerConnection() {
    console.log('Test broker connection function called');

    // Check if elements exist
    if (!connectionStatus) {
        console.error('Connection status element not found');
        alert('Connection status element not found');
        return;
    }

    // Show loading state
    console.log('Setting loading state');
    connectionStatus.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Testing connection...';
    connectionStatus.className = 'ms-3 text-info';

    if (connectionDetails) {
        connectionDetails.style.display = 'none';
    } else {
        console.error('Connection details element not found');
    }

    // Get current broker settings
    const broker = document.getElementById('broker') ? document.getElementById('broker').value : 'tastytrade';
    const apiKey = document.getElementById('api-key') ? document.getElementById('api-key').value : '';
    const apiSecret = document.getElementById('api-secret') ? document.getElementById('api-secret').value : '';
    const timeout = document.getElementById('connection-timeout') ? document.getElementById('connection-timeout').value : 10;

    console.log('Broker:', broker);
    console.log('Timeout:', timeout);

    // Send test request
    console.log('Sending test request to /api/debug/test_broker_connection');
    const requestData = {
        broker: broker,
        api_key: apiKey,
        api_secret: apiSecret,
        timeout: parseInt(timeout) || 10
    };
    console.log('Request data:', requestData);

    fetch('/api/debug/test_broker_connection', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        console.log('Response received:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);

        // Update status
        if (data.success) {
            console.log('Connection successful');
            connectionStatus.innerHTML = '<span class="text-success">✓ Connected successfully</span>';
            connectionStatus.className = 'ms-3 text-success';
        } else {
            console.log('Connection failed');
            connectionStatus.innerHTML = '<span class="text-danger">✗ Connection failed</span>';
            connectionStatus.className = 'ms-3 text-danger';
        }

        // Show details
        if (connectionDetailsText && connectionDetails) {
            connectionDetailsText.textContent = JSON.stringify(data.details, null, 2);
            connectionDetails.style.display = 'block';

            // Scroll to details
            connectionDetails.scrollIntoView({ behavior: 'smooth' });
        } else {
            console.error('Connection details elements not found');
        }
    })
    .catch(error => {
        console.error('Error testing connection:', error);
        connectionStatus.innerHTML = '<span class="text-danger">✗ Error testing connection</span>';
        connectionStatus.className = 'ms-3 text-danger';

        if (connectionDetailsText && connectionDetails) {
            connectionDetailsText.textContent = JSON.stringify({ error: error.toString() }, null, 2);
            connectionDetails.style.display = 'block';
        }
    });
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
        const bsAlert = new bootstrap.Alert(alertElement);
        bsAlert.close();
    }, 5000);
}
