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
        },

        lightFast: {
            triggers: [
                'ライトファースト', 'らいとふぁすと', 
                'ライト早く', 'らいと早く',
                'light fast', 'raito fast',
                '早い', 'ハヤイ',  // Simple "fast"
                'はやくして', 'ハヤクシテ',  // "make it fast"
                'ライトはやく', 'らいとはやく'  // More natural Japanese
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
                'ライトスロー', 'らいとすろー',
                'ライトゆっくり', 'らいとゆっくり',
                'light slow', 'raito slow',
                'おそい', 'オソイ',  // Simple "slow"
                'ゆっくり', 'ユックリ',  // "slowly"
                'ライトおそく', 'らいとおそく'  // More natural Japanese
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
        console.log('Looking for command match in:', lowerTranscript);
        
        for (const [cmdName, cmd] of Object.entries(this.commands)) {
            console.log('Checking command:', cmdName);
            const matched = cmd.triggers.some(trigger => {
                const isMatch = lowerTranscript.includes(trigger.toLowerCase());
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