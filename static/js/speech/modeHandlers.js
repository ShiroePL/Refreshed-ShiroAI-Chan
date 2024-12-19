import { CommandRegistry } from './commands.js';
import { TriggerCommandRegistry } from './triggerCommands.js';

export class ModeHandlers {
    static handleTriggerMode(transcript, switchToCommandMode) {
        console.log('Trigger mode received:', transcript);
        const command = TriggerCommandRegistry.findCommand(transcript);
        console.log('Found command:', command?.name);
        if (command) {
            console.log('Executing command:', command.name);
            return command.handler(transcript, switchToCommandMode);
        }
        return false;
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