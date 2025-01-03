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
    const contextSelect = document.getElementById('context-select');

    // Toggle settings panel
    settingsToggle.addEventListener('click', () => {
        settingsPanel.classList.add('open');
        loadAvailableContexts();
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
            // First save the context
            const saveResponse = await fetch('http://localhost:8014/context/update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ context_text: context }),
            });
            
            if (!saveResponse.ok) {
                const errorData = await saveResponse.json();
                throw new Error(errorData.detail || 'Failed to save context');
            }
            
            contextStatus.textContent = 'Context saved successfully!';
            contextStatus.style.color = '#4CAF50';
            
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

    // Load available contexts
    async function loadAvailableContexts() {
        try {
            const response = await fetch('http://localhost:8014/context/available');
            const data = await response.json();
            
            // Clear existing options
            contextSelect.innerHTML = '';
            
            // Add contexts to select
            data.contexts.forEach(context => {
                const option = document.createElement('option');
                option.value = context.id;
                // Show full context in title (tooltip on hover)
                option.title = context.text;
                // Show truncated version in dropdown
                option.text = context.text.length > 50 ? 
                    context.text.substring(0, 50) + '...' : 
                    context.text;
                option.selected = context.is_active;
                contextSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error loading contexts:', error);
            contextStatus.textContent = 'Error loading available contexts';
        }
    }

    // Handle context selection - show full text when selected
    contextSelect.addEventListener('change', async () => {
        const selectedId = contextSelect.value;
        try {
            const response = await fetch(`http://localhost:8014/context/activate/${selectedId}`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error('Failed to activate context');
            }
            
            contextStatus.textContent = 'Context activated successfully!';
            contextStatus.style.color = '#4CAF50';
            
            // Load the full selected context into the input
            const selectedOption = contextSelect.options[contextSelect.selectedIndex];
            contextInput.value = selectedOption.title;  // Use title which contains full text
            
        } catch (error) {
            console.error('Error activating context:', error);
            contextStatus.textContent = 'Error activating context';
            contextStatus.style.color = '#f44336';
        }
    });
}); 