export class TriggerCommandRegistry {
    static commands = {
        // Trigger words to start command mode
        wake: {
            triggers: [
                'hey shiro', 'hi shiro', 'hello shiro', 'hello', 'hey', 'hi',
                'wake up', 'wake up shiro',
                'good morning', 'good morning shiro'
            ],
            handler: (transcript, switchToCommandMode) => {
                const command = TriggerCommandRegistry.extractCommand(transcript);
                switchToCommandMode(command);
                return true;
            }
        },

        // System commands in trigger mode
        shutdown: {
            triggers: [
                'goodbye', 'goodbye shiro', 
                'bye', 'bye shiro',
                'shutdown', 'shut down'
            ],
            handler: (transcript, switchToCommandMode) => {
                switchToCommandMode('shutdown', true);
                return true;
            }
        },

        stop: {
            triggers: [
                'stop', 'stop it', 
                'be quiet', 'quiet',
                'shut up'
            ],
            handler: (transcript, switchToCommandMode) => {
                switchToCommandMode('stop', true);
                return true;
            }
        },

        lightFast: {
            triggers: [
                'change lights to fast', 'change lights to fast mode',
                'faster lights', 'speed up lights',
                'quick lights', 'faster'
            ],
            handler: (transcript, switchToCommandMode) => {
                console.log('light fast command triggered');
                window.socket.emit('action', { 
                    type: 'govee_lights',
                    mode: 'gdi'
                });
                return true;
            }
        },

        lightSlow: {
            triggers: [
                'light slow', 'lights slow',
                'change lights to slow', 'change lights to slow mode',
                'slower lights', 'slow down lights',
                'gentle lights', 'slower'
            ],
            handler: (transcript, switchToCommandMode) => {
                console.log('light slow command triggered');
                window.socket.emit('action', { 
                    type: 'govee_lights',
                    mode: 'dxgi'
                });
                return true;
            }
        }
    };

    static extractCommand(transcript) {
        const allTriggers = this.commands.wake.triggers;
        return allTriggers.reduce((text, trigger) => {
            const parts = text.toLowerCase().split(trigger.toLowerCase());
            return parts.length > 1 ? parts.pop().trim() : text;
        }, transcript);
    }

    static findCommand(transcript) {
        const lowerTranscript = transcript.toLowerCase().trim();
        
        for (const [cmdName, cmd] of Object.entries(this.commands)) {
            const matched = cmd.triggers.some(trigger => {
                const isMatch = lowerTranscript === trigger.toLowerCase();
                if (isMatch) console.log('Matched trigger:', trigger);
                return isMatch;
            });
            if (matched) {
                console.log('Found matching command:', cmdName);
                return {
                    name: cmdName,
                    handler: cmd.handler
                };
            }
        }
        console.log('No command match found');
        return null;
    }

    static addCommand(name, triggers, handler) {
        this.commands[name] = { triggers, handler };
    }
} 