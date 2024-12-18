import { AudioFeedback } from './audioFeedback.js';
import { UIHandler } from './uiHandler.js';
import { RecognitionStates } from './states.js';

export class ModeHandlers {
    static handleTriggerMode(transcript, switchToCommandMode) {
        const triggerWords = [
            'hi shiro', 
            'はい シロ', 
            'hi シロ', 
            'はいシロ', 
            'はいしろ', 
            'ハイシロ',
            'おはよう',  // Good morning in hiragana
            'オハヨウ',  // Good morning in katakana
            'おはようシロ',  // Good morning Shiro in hiragana
            'オハヨウシロ'   // Good morning Shiro in katakana
        ];

        const shutdownWords = [
            'sayounara',     // Goodbye in romaji
            'さようなら',     // Goodbye in hiragana
            'サヨウナラ',     // Goodbye in katakana
            'さようならシロ', // Goodbye Shiro in hiragana
            'サヨウナラシロ'  // Goodbye Shiro in katakana
        ];

        const lowerTranscript = transcript.toLowerCase();
        
        // Check for shutdown command first
        const isShutdown = shutdownWords.some(word => 
            lowerTranscript.includes(word.toLowerCase())
        );

        if (isShutdown) {
            // Directly emit stop_listening instead of going through command mode
            switchToCommandMode('shutdown', true);
            return true;
        }

        // Check for regular trigger words
        const triggered = triggerWords.some(trigger => 
            lowerTranscript.includes(trigger.toLowerCase())
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

    static handleCommandMode(transcript, socket, switchToTriggerMode) {
        // Special handling for shutdown command
        if (transcript === 'shutdown') {
            socket.emit('stop_listening');
            return; // Don't switch modes, let the shutdown_complete event handle it
        }
        socket.emit('transcript', { transcript: transcript });
        switchToTriggerMode();
    }

    static handlePushToTalk(transcript, socket) {
        socket.emit('transcript', { transcript: transcript });
    }
} 