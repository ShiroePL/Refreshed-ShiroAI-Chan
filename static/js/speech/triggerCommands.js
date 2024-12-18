export class TriggerCommandRegistry {
    static commands = {
        // Trigger words to start English mode
        wake: {
            triggers: [
                'hi shiro', 'はい シロ', 'hi シロ', 
                'はいシロ', 'はいしろ', 'ハイシロ',
                'おはよう', 'オハヨウ', 
                'おはようシロ', 'オハヨウシロ'
            ],
            handler: (transcript, switchToCommandMode) => {
                const command = TriggerCommandRegistry.extractCommand(transcript);
                switchToCommandMode(command);
                return true;
            }
        },

        // System commands in Japanese mode
        shutdown: {
            triggers: [
                'sayounara', 'さようなら', 'さよなら', 
                'サヨウナラ', 'さようならシロ', 'サヨウナラシロ'
            ],
            handler: (transcript, switchToCommandMode) => {
                switchToCommandMode('shutdown', true);
                return true;
            }
        },

        stop: {
            triggers: [
                'stop', 'ストップ', 'スタップ', 
                'すとっぷ', 'とめて', 'やめて'
            ],
            handler: (transcript, switchToCommandMode) => {
                switchToCommandMode('stop', true);
                return true;
            }
        }

        // Add more Japanese commands here
        // Example:
        // lightControl: {
        //     triggers: ['ライト', 'らいと', '電気'],
        //     handler: (transcript, switchToCommandMode) => {
        //         // Handle light control directly in Japanese mode
        //         return true;
        //     }
        // }
    };

    static extractCommand(transcript) {
        const allTriggers = this.commands.wake.triggers;
        return allTriggers.reduce((text, trigger) => {
            const parts = text.toLowerCase().split(trigger.toLowerCase());
            return parts.length > 1 ? parts.pop().trim() : text;
        }, transcript);
    }

    static findCommand(transcript) {
        const lowerTranscript = transcript.toLowerCase();
        
        for (const [cmdName, cmd] of Object.entries(this.commands)) {
            if (cmd.triggers.some(trigger => 
                lowerTranscript.includes(trigger.toLowerCase())
            )) {
                return {
                    name: cmdName,
                    handler: cmd.handler
                };
            }
        }
        return null;
    }

    static addCommand(name, triggers, handler) {
        this.commands[name] = { triggers, handler };
    }
} 