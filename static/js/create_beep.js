// This is a script to generate a beep sound using Web Audio API
// We'll generate a beep sound and download it

// Set up audio context
const audioContext = new (window.AudioContext || window.webkitAudioContext)();
const duration = 0.2; // Duration in seconds
const frequency = 800; // Beep frequency in Hz
const volume = 0.5; // Volume (0-1)

// Create oscillator
const oscillator = audioContext.createOscillator();
oscillator.type = 'square'; // Square wave for a more "beep" sound
oscillator.frequency.value = frequency;

// Create gain node for volume control
const gainNode = audioContext.createGain();
gainNode.gain.value = volume;

// Connect nodes
oscillator.connect(gainNode);
gainNode.connect(audioContext.destination);

// Start recording
const startTime = audioContext.currentTime;
oscillator.start(startTime);
oscillator.stop(startTime + duration);

// Create a buffer to store the audio data
const sampleRate = audioContext.sampleRate;
const bufferLength = Math.ceil(duration * sampleRate);
const audioBuffer = audioContext.createBuffer(1, bufferLength, sampleRate);
const channelData = audioBuffer.getChannelData(0);

// Fill the buffer with a square wave
for (let i = 0; i < bufferLength; i++) {
    const time = i / sampleRate;
    channelData[i] = time % (1 / frequency) < (1 / frequency / 2) ? volume : -volume;
}

// Export the buffer as a WAV file
function encodeWav(audioBuffer) {
    const numChannels = audioBuffer.numberOfChannels;
    const sampleRate = audioBuffer.sampleRate;
    const bitDepth = 16; // 16-bit audio
    const bytesPerSample = bitDepth / 8;
    const blockAlign = numChannels * bytesPerSample;
    const byteRate = sampleRate * blockAlign;
    const dataSize = audioBuffer.length * blockAlign;
    const buffer = new ArrayBuffer(44 + dataSize);
    const view = new DataView(buffer);

    // RIFF chunk descriptor
    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + dataSize, true);
    writeString(view, 8, 'WAVE');

    // FMT sub-chunk
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true); // Subchunk size
    view.setUint16(20, 1, true); // PCM format
    view.setUint16(22, numChannels, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, byteRate, true);
    view.setUint16(32, blockAlign, true);
    view.setUint16(34, bitDepth, true);

    // Data sub-chunk
    writeString(view, 36, 'data');
    view.setUint32(40, dataSize, true);

    // Write audio data
    const offset = 44;
    const channelData = [];
    for (let i = 0; i < numChannels; i++) {
        channelData[i] = audioBuffer.getChannelData(i);
    }

    for (let i = 0; i < audioBuffer.length; i++) {
        for (let channel = 0; channel < numChannels; channel++) {
            const sample = Math.max(-1, Math.min(1, channelData[channel][i]));
            const value = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
            view.setInt16(offset + (i * blockAlign) + (channel * bytesPerSample), value, true);
        }
    }

    return buffer;
}

function writeString(view, offset, string) {
    for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
    }
}

// Create a download link
const blob = new Blob([encodeWav(audioBuffer)], { type: 'audio/wav' });
const url = URL.createObjectURL(blob);
const a = document.createElement('a');
a.style.display = 'none';
a.href = url;
a.download = 'beep.wav';
document.body.appendChild(a);
a.click();
URL.revokeObjectURL(url);