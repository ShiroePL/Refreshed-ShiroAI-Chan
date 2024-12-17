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
        const lowerTranscript = transcript.toLowerCase();
        
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
        socket.emit('transcript', { transcript: transcript });
        switchToTriggerMode();
    }

    static handlePushToTalk(transcript, socket) {
        socket.emit('transcript', { transcript: transcript });
    }
} 