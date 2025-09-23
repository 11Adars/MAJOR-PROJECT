// Defer element queries until DOM is ready
let videoElement, canvasElement, canvasCtx, enableWebcamButton;

function initDomRefs() {
    videoElement = document.querySelector('.input_video');
    canvasElement = document.querySelector('.output_canvas');
    enableWebcamButton = document.getElementById('camButton');
    if (!videoElement || !canvasElement || !enableWebcamButton) {
        console.error('Required DOM elements missing');
        return false;
    }
    canvasCtx = canvasElement.getContext('2d');
    return true;
}

// Simplified: remove dictionary, modal, and online toggle. Default offline endpoint.
const OFFLINE_ENDPOINT = 'http://127.0.0.1:8000/islr/predict';

// Initialize MediaPipe Holistic model
const holistic = new Holistic({
    locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/holistic/${file}`
});

// Configure Holistic model options
holistic.setOptions({
    modelComplexity: 1,
    smoothLandmarks: true,
    refineFaceLandmarks: true,
    minDetectionConfidence: 0.5,
    minTrackingConfidence: 0.5
});

// Frame counter, landmark data collection, and API call status
let frameCount = 0;
let landmarkData = [];
let sampleEvery = 1; // adaptive sampling factor
let lastSendTime = performance.now();
let isApiCallInProgress = false;

function adjustCanvasSize() {
    if (!canvasElement || !videoElement) return;
    const screenWidth = window.innerWidth;
    const size = screenWidth <= 768 ? Math.floor(screenWidth * 0.9) : 480;
    canvasElement.width = size;
    canvasElement.height = size;
    videoElement.width = size;
    videoElement.height = size;
}

let camera;

// Enable webcam and start processing with error handling
function enableCam() {
    if (!initDomRefs()) return;
    enableWebcamButton.disabled = true;
    enableWebcamButton.textContent = 'Starting...';
    holistic.onResults(onResults);
    try {
        if (!camera) {
            camera = new Camera(videoElement, {
                onFrame: async () => await holistic.send({ image: videoElement }),
                width: canvasElement.width,
                height: canvasElement.height
            });
        }
        camera.start();
        enableWebcamButton.style.display = 'none';
    } catch (err) {
        console.error('Camera start failed:', err);
        enableWebcamButton.disabled = false;
        enableWebcamButton.textContent = 'Enable Webcam';
        const predEl = document.getElementById('pred');
        if (predEl) predEl.textContent = 'Camera error: ' + (err.message || err);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (!initDomRefs()) return;
    adjustCanvasSize();
    window.addEventListener('resize', adjustCanvasSize);
    enableWebcamButton.textContent = 'Enable Webcam';
    enableWebcamButton.addEventListener('click', enableCam);
});

// Update the sendLandmarkData function to use the selected API endpoint
async function sendLandmarkData(data) {
    isApiCallInProgress = true;

  const apiEndpoint = OFFLINE_ENDPOINT;

    try {
        const response = await fetch(apiEndpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });

        if (response.ok) {
            const result = await response.json();
            document.getElementById("pred").textContent = result.sign;
            document.getElementById("pred_sentence").textContent = result.sentence;
            console.log('Response from API:', result);
        } else {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
    } catch (error) {
        console.error('Error in sending data:', error);
    } finally {
        isApiCallInProgress = false;
    }
}

// No dynamic endpoint UI needed now.

// Global flag to track skeleton drawing (hands + pose only)
let drawSkeleton = true;

// Process results and draw landmarks
function onResults(results) {
    canvasCtx.save();
    canvasCtx.translate(canvasElement.width, 0);
    canvasCtx.scale(-1, 1);
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);

    canvasCtx.globalCompositeOperation = 'destination-atop';
    canvasCtx.drawImage(results.image, 0, 0, canvasElement.width, canvasElement.height);

    if (drawSkeleton) {
      // Define color and line width variables
      const lineColor = '#FFFFFF';
      const circleColor = '#04D9FF';
  
      const connectorWidth = 1;
      const landmarkWidth = 1;
      const landmarkRadius = 3;
  
      // Set global composite operation
      canvasCtx.globalCompositeOperation = 'source-over';
  
      // Draw landmarks and connectors with unified colors
      drawConnectors(canvasCtx, results.poseLandmarks, POSE_CONNECTIONS, {
          color: lineColor,
          lineWidth: connectorWidth,
          radius: landmarkRadius
      });
      drawLandmarks(canvasCtx, results.poseLandmarks, {
          color: circleColor,
          lineWidth: landmarkWidth,
          radius: landmarkRadius
      });
    // Face mesh intentionally omitted for less visual clutter.
      drawConnectors(canvasCtx, results.leftHandLandmarks, HAND_CONNECTIONS, {
          color: lineColor,
          lineWidth: connectorWidth,
          radius: landmarkRadius
      });
      drawLandmarks(canvasCtx, results.leftHandLandmarks, {
          color: circleColor,
          lineWidth: landmarkWidth,
          radius: landmarkRadius
      });
      drawConnectors(canvasCtx, results.rightHandLandmarks, HAND_CONNECTIONS, {
          color: lineColor,
          lineWidth: connectorWidth,
          radius: landmarkRadius
      });
      drawLandmarks(canvasCtx, results.rightHandLandmarks, {
          color: circleColor,
          lineWidth: landmarkWidth,
          radius: landmarkRadius
      });
  }

    canvasCtx.restore();

    canvasElement.style.opacity = isApiCallInProgress ? "0.5" : "1";

    if (isApiCallInProgress) return;

    frameCount++;
    const timeInSeconds = (performance.now() / 1000).toFixed(2);

        // Adaptive sampling: reduce frequency for high thresholds
        const threshold = parseInt(predictionSpeedSlider.value, 10);
        sampleEvery = threshold > 40 ? 2 : 1;
        if (frameCount % sampleEvery === 0) {
            const roundLm = (lmArr) => lmArr ? lmArr.map(lm => ({
                x: +lm.x.toFixed(4),
                y: +lm.y.toFixed(4),
                z: lm.z !== undefined ? +lm.z.toFixed(4) : undefined,
                visibility: lm.visibility !== undefined ? +lm.visibility.toFixed(4) : undefined
            })) : null;
            landmarkData.push({
                    timeInSeconds,
                    frameNumber: frameCount,
                    poseLandmarks: roundLm(results.poseLandmarks),
                    faceLandmarks: null, // not used; omit to shrink payload
                    leftHandLandmarks: roundLm(results.leftHandLandmarks),
                    rightHandLandmarks: roundLm(results.rightHandLandmarks),
            });
        }

    // Dynamically update frame count threshold
    const predictionSpeed = threshold;
    if (frameCount >= predictionSpeed) {
        sendLandmarkData(landmarkData);
        landmarkData = [];
        frameCount = 0;
        lastSendTime = performance.now();
    }
}

// Initialize slider
const predictionSpeedSlider = document.getElementById('predictionSpeed');
const sliderValueDisplay = document.getElementById('sliderValue');

// Update slider value display
predictionSpeedSlider.addEventListener('input', () => {
    sliderValueDisplay.textContent = predictionSpeedSlider.value;
});

// Particles and other decorative elements removed.