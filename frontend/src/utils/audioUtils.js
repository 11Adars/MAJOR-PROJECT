export const audioConfig = {
  sampleRate: 44100,
  channelCount: 1,
  bitsPerSample: 16
};

export const processAudio = async (audioBlob) => {
  try {
    const audioContext = new AudioContext({
      sampleRate: audioConfig.sampleRate
    });

    // Convert blob to array buffer
    const arrayBuffer = await audioBlob.arrayBuffer();
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
    
    // Process chunks in smaller batches to prevent stack overflow
    const channelData = audioBuffer.getChannelData(0);
    const batchSize = 1024;
    const normalizedData = new Float32Array(channelData.length);
    
    // Find max value for normalization
    let maxValue = 0;
    for (let i = 0; i < channelData.length; i++) {
      maxValue = Math.max(maxValue, Math.abs(channelData[i]));
    }

    // Normalize in batches
    for (let i = 0; i < channelData.length; i += batchSize) {
      const end = Math.min(i + batchSize, channelData.length);
      for (let j = i; j < end; j++) {
        normalizedData[j] = channelData[j] / maxValue;
      }
    }

    // Create WAV file
    const wavBuffer = new ArrayBuffer(44 + normalizedData.length * 2);
    const view = new DataView(wavBuffer);

    // Write WAV header
    writeWavHeader(view, normalizedData.length);

    // Write audio data in batches
    let offset = 44;
    for (let i = 0; i < normalizedData.length; i += batchSize) {
      const end = Math.min(i + batchSize, normalizedData.length);
      for (let j = i; j < end; j++) {
        const sample = Math.max(-1, Math.min(1, normalizedData[j]));
        view.setInt16(offset, sample * 0x7FFF, true);
        offset += 2;
      }
    }

    return new Blob([wavBuffer], { type: 'audio/wav' });
  } catch (err) {
    console.error('Audio processing error:', err);
    throw new Error('Failed to process audio: ' + err.message);
  }
};

function writeWavHeader(view, length) {
  const { sampleRate, channelCount, bitsPerSample } = audioConfig;
  
  // RIFF chunk descriptor
  writeString(view, 0, 'RIFF');
  view.setUint32(4, 36 + length * 2, true);
  writeString(view, 8, 'WAVE');

  // fmt sub-chunk
  writeString(view, 12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM format
  view.setUint16(22, channelCount, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * channelCount * bitsPerSample / 8, true);
  view.setUint16(32, channelCount * bitsPerSample / 8, true);
  view.setUint16(34, bitsPerSample, true);

  // data sub-chunk
  writeString(view, 36, 'data');
  view.setUint32(40, length * 2, true);
}

function writeString(view, offset, string) {
  for (let i = 0; i < string.length; i++) {
    view.setUint8(offset + i, string.charCodeAt(i));
  }
}