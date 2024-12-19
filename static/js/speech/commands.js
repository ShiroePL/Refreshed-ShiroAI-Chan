// Command types
export const CommandType = {
    SYSTEM: 'system',    // System commands like shutdown, stop, etc.
    ACTION: 'action',    // Actions that trigger Python backend scripts
    CHAT: 'chat'        // Normal chat interactions
};

// Command registry
export class CommandRegistry {
    static commands = {
        // System commands
        system: {
            stop: {
                triggers: ['stop', 'ストップ','スタップ', 'すとっぷ', 'とめて', 'やめて'],
                handler: (socket, socketHandler) => {
                    console.log('Stop command triggered');
                    console.log('Is playing?', socketHandler?.isCurrentlyPlaying());
                    if (socketHandler?.isCurrentlyPlaying()) {
                        console.log('Stopping audio...');
                        socketHandler.stopCurrentAudio();
                        socket.emit('audio_finished');
                    }
                    return { switchToTrigger: true };
                }
            }
        },
        
        // Action commands that trigger Python backend
        action: {
            lights: {
                triggers: ['change lights mode', 'lights mode', 'switch lights'],
                handler: (socket) => {
                    console.log('light mode');
                    socket.emit('action', { type: 'lights_mode' });
                    return { switchToTrigger: true };
                }
                
            },
            music: {
                triggers: ['play music', 'start music', 'music please'],
                handler: (socket) => {
                    console.log('music mode');
                    socket.emit('action', { type: 'play_music' });
                    return { switchToTrigger: true };
                }
            }
        },
        
        // Default chat handling
        chat: {
            default: {
                handler: (socket, _socketHandler, transcript) => {
                    // Send only the necessary data
                    socket.emit('transcript', { 
                        transcript: transcript.toString() 
                    });
                    return { switchToTrigger: true };
                }
            }
        }
    };

    static findCommand(transcript, type = null) {
        try {
            const lowerTranscript = transcript.toString().toLowerCase();
            
            // If type is specified, only search in that category
            const categoriesToSearch = type ? [type] : ['system', 'action'];
            
            for (const category of categoriesToSearch) {
                const commands = this.commands[category];
                for (const [cmdName, cmd] of Object.entries(commands)) {
                    if (cmd.triggers && cmd.triggers.some(trigger => 
                        lowerTranscript.includes(trigger.toLowerCase())
                    )) {
                        return { 
                            type: category,
                            name: cmdName,
                            handler: cmd.handler 
                        };
                    }
                }
            }
            
            // Return default chat handler if no command found
            return {
                type: 'chat',
                name: 'default',
                handler: this.commands.chat.default.handler
            };
        } catch (error) {
            console.error('Error finding command:', error);
            return null;
        }
    }

    static addCommand(type, name, triggers, handler) {
        if (!this.commands[type]) {
            this.commands[type] = {};
        }
        this.commands[type][name] = { triggers, handler };
    }
} 