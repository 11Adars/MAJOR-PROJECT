// Simple Sign Language Recognition Script
console.log("🚀 Script loading started");

const videoElement = document.querySelector('.input_video');
const canvasElement = document.querySelector('.output_canvas');
const canvasCtx = canvasElement.getContext('2d');
const enableWebcamButton = document.getElementById("camButton");
const predictionDisplay = document.getElementById("pred");
const sentenceDisplay = document.getElementById("pred_sentence");

// Debug: Check if DOM elements are found
console.log("DOM Elements Check:");
console.log("videoElement:", videoElement);
console.log("predictionDisplay:", predictionDisplay);
console.log("sentenceDisplay:", sentenceDisplay);
console.log("enableWebcamButton:", enableWebcamButton);

// Test DOM manipulation immediately
if (predictionDisplay) {
    predictionDisplay.textContent = "🟢 JavaScript Loaded Successfully!";
    predictionDisplay.style.color = "green";
} else {
    console.error("❌ predictionDisplay element not found");
}

if (sentenceDisplay) {
    sentenceDisplay.textContent = "🟢 Script is working!";
    sentenceDisplay.style.color = "blue";
} else {
    console.error("❌ sentenceDisplay element not found");
}

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

// Frame counter and landmark data collection
let frameCount = 0;
let landmarkData = [];
let isApiCallInProgress = false;

// Adjust canvas and video dimensions
function adjustCanvasSize() {
    const video = videoElement;
    const canvas = canvasElement;
    
    if (video.videoWidth && video.videoHeight) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.style.width = '100%';
        canvas.style.height = 'auto';
    }
}

// Initialize camera
const camera = new Camera(videoElement, {
    onFrame: async () => await holistic.send({ image: videoElement }),
    width: 640,
    height: 480
});

// Enable webcam functionality
function enableCam() {
    if (!camera) {
        console.error("Camera not initialized");
        return;
    }
    
    enableWebcamButton.disabled = true;
    enableWebcamButton.innerHTML = "Starting Camera...";
    
    camera.start().then(() => {
        enableWebcamButton.innerHTML = "Camera Active";
        enableWebcamButton.style.background = "linear-gradient(45deg, #4CAF50, #45a049)";
        console.log("Camera started successfully");
    }).catch((error) => {
        console.error("Error starting camera:", error);
        enableWebcamButton.innerHTML = "Camera Error - Retry";
        enableWebcamButton.disabled = false;
    });
}

// Send landmark data to backend
async function sendLandmarkData(data) {
    if (isApiCallInProgress) return;
    
    console.log("Sending landmark data to server:", data.length, "frames");
    isApiCallInProgress = true;
    
    try {
        const response = await fetch('/islr/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log("Received prediction result:", result);
        console.log("Sign:", result.sign, "Sentence:", result.sentence, "Confidence:", result.confidence);
        
        // Update prediction display
        console.log("Updating prediction display...");
        if (result.sign) {
            console.log("Processing sign:", result.sign);
            // Handle no_action specially - show status but don't add to sentence
            if (result.sign === "no_action") {
                console.log("Setting no_action display");
                predictionDisplay.textContent = "No gesture detected";
                predictionDisplay.style.color = "#888"; // Gray color for no action
            } else {
                console.log("Setting gesture display:", result.sign);
                predictionDisplay.textContent = result.sign;
                predictionDisplay.style.color = "#4CAF50"; // Green for detected gestures
                predictionDisplay.classList.add('updated');
                setTimeout(() => predictionDisplay.classList.remove('updated'), 500);
            }
        } else {
            console.log("No sign field in result");
        }
        
        // Update sentence display - show current sentence regardless of current sign
        console.log("Updating sentence display...");
        if (result.sentence) {
            console.log("Setting sentence:", result.sentence);
            sentenceDisplay.textContent = result.sentence;
            sentenceDisplay.classList.add('updated');
            setTimeout(() => sentenceDisplay.classList.remove('updated'), 500);
        } else {
            console.log("No sentence field in result");
        }
        
    } catch (error) {
        console.error('Error sending landmark data:', error);
        predictionDisplay.textContent = "Error in prediction";
    } finally {
        isApiCallInProgress = false;
    }
}

// Process MediaPipe results
function onResults(results) {
    // Clear canvas
    canvasCtx.save();
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    
    // Draw the video frame
    canvasCtx.drawImage(results.image, 0, 0, canvasElement.width, canvasElement.height);
    
    // Draw landmarks
    if (results.faceLandmarks) {
        drawConnectors(canvasCtx, results.faceLandmarks, FACEMESH_CONTOURS, {color: '#C0C0C070', lineWidth: 1});
    }
    
    if (results.poseLandmarks) {
        drawConnectors(canvasCtx, results.poseLandmarks, POSE_CONNECTIONS, {color: '#00FF00', lineWidth: 4});
        drawLandmarks(canvasCtx, results.poseLandmarks, {color: '#FF0000', lineWidth: 2});
    }
    
    if (results.leftHandLandmarks) {
        drawConnectors(canvasCtx, results.leftHandLandmarks, HAND_CONNECTIONS, {color: '#CC0000', lineWidth: 5});
        drawLandmarks(canvasCtx, results.leftHandLandmarks, {color: '#00FF00', lineWidth: 2});
    }
    
    if (results.rightHandLandmarks) {
        drawConnectors(canvasCtx, results.rightHandLandmarks, HAND_CONNECTIONS, {color: '#00CC00', lineWidth: 5});
        drawLandmarks(canvasCtx, results.rightHandLandmarks, {color: '#FF0000', lineWidth: 2});
    }
    
    canvasCtx.restore();
    
    // Collect landmark data for prediction
    frameCount++;
    const currentTime = performance.now() / 1000;
    
    const frameData = {
        timeInSeconds: currentTime,
        frameNumber: frameCount,
        poseLandmarks: results.poseLandmarks || null,
        faceLandmarks: results.faceLandmarks || null,
        leftHandLandmarks: results.leftHandLandmarks || null,
        rightHandLandmarks: results.rightHandLandmarks || null
    };
    
    // Log landmark detection
    if (results.poseLandmarks || results.leftHandLandmarks || results.rightHandLandmarks) {
        console.log(`Frame ${frameCount}: Detected landmarks - Pose: ${!!results.poseLandmarks}, Left Hand: ${!!results.leftHandLandmarks}, Right Hand: ${!!results.rightHandLandmarks}`);
    }
    
    landmarkData.push(frameData);
    
    // Send data every 30 frames (approximately every second at 30 FPS)
    if (frameCount % 30 === 0 && landmarkData.length > 0) {
        console.log(`Sending data after ${frameCount} frames`);
        sendLandmarkData([...landmarkData]);
        landmarkData = []; // Clear the buffer
    }
}

// Set up MediaPipe results handler
holistic.onResults(onResults);

// Initialize the application
enableWebcamButton.addEventListener("click", enableCam);

// Adjust canvas size when video loads
videoElement.addEventListener('loadedmetadata', adjustCanvasSize);
window.addEventListener("resize", adjustCanvasSize);
