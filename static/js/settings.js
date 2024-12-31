const DEBUG = true;

function log(...args) {
    if (DEBUG) console.log('[Settings]', ...args);
}

document.addEventListener('DOMContentLoaded', function() {
    const settingsPanel = document.getElementById('settings-panel');
    const settingsToggle = document.getElementById('settings-toggle');
    const closeSettings = document.getElementById('close-settings');
    const saveContext = document.getElementById('save-context');
    const contextInput = document.getElementById('context-input');
    const contextStatus = document.getElementById('context-status');

    // Toggle settings panel
    settingsToggle.addEventListener('click', () => {
        settingsPanel.classList.add('open');
        loadCurrentContext();
    });

    closeSettings.addEventListener('click', () => {
        settingsPanel.classList.remove('open');
    });

    // Load current context when opening settings
    async function loadCurrentContext() {
        try {
            const response = await fetch('http://localhost:8014/context/current');
            const data = await response.json();
            contextInput.value = data.context || '';
        } catch (error) {
            console.error('Error loading context:', error);
            contextStatus.textContent = 'Error loading current context';
        }
    }

    // Save context
    saveContext.addEventListener('click', async () => {
        const context = contextInput.value;
        log('Saving context:', context);
        try {
            const response = await fetch('http://localhost:8014/context/update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ context_text: context }),
            });
            log('Response:', response);

            if (response.ok) {
                const data = await response.json();
                log('Success data:', data);
                contextStatus.textContent = 'Context saved successfully!';
                contextStatus.style.color = '#4CAF50';
            } else {
                const errorData = await response.json();
                log('Error data:', errorData);
                throw new Error(errorData.detail || 'Failed to save context');
            }
        } catch (error) {
            console.error('Error saving context:', error);
            contextStatus.textContent = 'Error saving context';
            contextStatus.style.color = '#f44336';
        }
    });

    // Close settings when clicking outside
    document.addEventListener('click', (event) => {
        if (!settingsPanel.contains(event.target) && 
            !settingsToggle.contains(event.target) && 
            settingsPanel.classList.contains('open')) {
            settingsPanel.classList.remove('open');
        }
    });
}); 