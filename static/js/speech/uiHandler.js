import { RecognitionStates } from './states.js';

export class UIHandler {
    static updateStatus(state) {
        const statusElement = document.getElementById('listening-status');
        const pushToTalkBtn = document.getElementById('pushToTalkBtn');

        // Update push-to-talk button
        const isPushToTalk = state === RecognitionStates.PUSH_TO_TALK;
        pushToTalkBtn.classList.toggle('btn-danger', isPushToTalk);
        pushToTalkBtn.classList.toggle('btn-info', !isPushToTalk);

        // Update status text
        switch (state) {
            case RecognitionStates.IDLE:
                statusElement.textContent = 'Not Listening';
                statusElement.className = 'status-inactive';
                break;
            case RecognitionStates.LISTENING_FOR_TRIGGER:
                statusElement.textContent = 'Listening for: "Hi Shiro" / "はい シロ"';
                statusElement.className = 'status-active';
                break;
            case RecognitionStates.LISTENING_FOR_COMMAND:
                statusElement.textContent = 'Listening in English...';
                statusElement.className = 'status-active';
                break;
            case RecognitionStates.PUSH_TO_TALK:
                statusElement.textContent = 'Push-to-Talk Active';
                statusElement.className = 'status-active';
                break;
            case RecognitionStates.ERROR:
                statusElement.textContent = 'Error - Retrying...';
                statusElement.className = 'status-inactive';
                break;
            case RecognitionStates.STARTING:
                statusElement.textContent = 'Starting...';
                statusElement.className = 'status-active';
                break;
        }
    }
} 