export function startRecording(setBlob) {
    navigator.mediaDevices.getUserMedia({ 
        audio: {
            channelCount: 1,
            sampleRate: 16000,
            sampleSize: 16,
            volume: 1.0,
            noiseSuppression: true,
            echoCancellation: true
        } 
    })
    .then(stream => {
        const mediaRecorder = new MediaRecorder(stream, {
            audioBitsPerSecond: 128000
        });
        const audioChunks = [];

        mediaRecorder.ondataavailable = event => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            setBlob(audioBlob);
        };

        mediaRecorder.start();

        setTimeout(() => {
            mediaRecorder.stop();
            stream.getTracks().forEach(track => track.stop());
        }, 9000); // Record for 9 seconds for better voice sample
    })
    .catch(err => {
        console.error('Microphone access denied or error:', err);
        alert('Microphone access is required!');
    });
}