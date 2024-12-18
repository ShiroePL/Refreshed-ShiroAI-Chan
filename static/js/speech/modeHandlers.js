import { CommandRegistry } from './commands.js';

export class ModeHandlers {
    static handleTriggerMode(transcript, switchToCommandMode) {
        const triggerWords = [
            'hi shiro', 'はい シロ', 'hi シロ', 'はいシロ', 'はいしろ', 'ハイシロ',
            'おはよう', 'オハヨウ', 'おはようシロ', 'オハヨウシロ'
        ];

        // Check for shutdown command first
        const shutdownWords = ['sayounara', 'さようなら', 'さよなら', 'サヨウナラ', 'さようならシロ', 'サヨウナラシロ'];
        const isShutdown = shutdownWords.some(word => 
            transcript.toLowerCase().includes(word.toLowerCase())
        );

        // Check for stop command
        const stopWords = ['stop', 'ストップ', 'スタップ', 'すとっぷ', 'とめて', 'やめて'];
        const isStopCommand = stopWords.some(word => 
            transcript.toLowerCase().includes(word.toLowerCase())
        );

        if (isShutdown) {
            switchToCommandMode('shutdown', true);
            return true;
        }

        if (isStopCommand) {
            console.log('Stop command detected in trigger mode');
            switchToCommandMode('stop', true);  // Add second parameter to indicate special command
            return true;
        }

        const triggered = triggerWords.some(trigger => 
            transcript.toLowerCase().includes(trigger.toLowerCase())
        );

        if (triggered) {
            const command = triggerWords.reduce((text, trigger) => {
                const parts = text.toLowerCase().split(trigger.toLowerCase());
                return parts.length > 1 ? parts.pop().trim() : text;
            }, transcript);

            switchToCommandMode(command);
        }
        return triggered;
    }

    static handleCommandMode(transcript, socket, socketHandler, switchToTriggerMode) {
        try {
            // Special handling for direct commands
            if (transcript === 'stop') {
                console.log('Processing stop command');
                if (socketHandler?.isCurrentlyPlaying()) {
                    socketHandler.stopCurrentAudio();
                }
                switchToTriggerMode();
                return;
            }

            // Process other commands normally
            const command = CommandRegistry.findCommand(transcript);
            if (!command) {
                socket.emit('transcript', { transcript: transcript.toString() });
                switchToTriggerMode();
                return;
            }

            const result = command.handler(socket, socketHandler, transcript);
            
            if (result?.skipCommandMode) return;
            if (result?.switchToTrigger) switchToTriggerMode();
        } catch (error) {
            console.error('Error handling command:', error);
            socket.emit('transcript', { transcript: transcript.toString() });
            switchToTriggerMode();
        }
    }
} 