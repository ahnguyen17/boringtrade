// BoringTrade Configuration JavaScript

// DOM elements
const configForm = document.getElementById('config-form');
const resetConfigBtn = document.getElementById('reset-config-btn');

// Initialize configuration page
document.addEventListener('DOMContentLoaded', () => {
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
