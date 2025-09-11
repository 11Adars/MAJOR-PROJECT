class CustomGesturesApp {
    constructor() {
        this.holistic = null;
        this.camera = null;
        this.webcamElement = document.getElementById('webcam');
        this.canvasElement = document.getElementById('canvas');
        this.canvasCtx = this.canvasElement.getContext('2d');
        
        this.isRunning = false;
        this.frameData = [];
        this.frameCount = 0;
        this.startTime = null;
        
        this.serverUrl = 'http://127.0.0.1:8002';
        
        this.initializeApp();
    }

    async initializeApp() {
        await this.checkServerStatus();
        this.setupEventListeners();
        this.initializeMediaPipe();
    }

    async checkServerStatus() {
        try {
            const response = await fetch(`${this.serverUrl}/health`);
            const data = await response.json();
            
            // Update connection status
            const connectionStatus = document.getElementById('connection-status');
            connectionStatus.textContent = data.model_loaded ? 'Connected' : 'Error';
            
            // Update model technology
            const modelTech = document.getElementById('model-tech');
            const techParts = [];
            if (data.model_info?.has_lstm) techParts.push('LSTM');
            if (data.model_info?.has_classifier) techParts.push('RandomForest');
            modelTech.textContent = techParts.join(' + ') || 'None';
            
            // Update gesture count
            const gestureCount = document.getElementById('gesture-count');
            gestureCount.textContent = data.model_info?.gestures?.length || 0;
            
            // Load gestures list
            await this.loadGesturesList();
            
        } catch (error) {
            console.error('Server connection failed:', error);
            const connectionStatus = document.getElementById('connection-status');
            connectionStatus.textContent = 'Disconnected';
        }
    }

    async loadGesturesList() {
        try {
            const response = await fetch(`${this.serverUrl}/info`);
            const data = await response.json();
            
            const gesturesList = document.getElementById('gestures-list');
            if (data.available_gestures && data.available_gestures.length > 0) {
                gesturesList.innerHTML = data.available_gestures
                    .map(gesture => `<div class="gesture-item">${gesture}</div>`)
                    .join('');
            } else {
                gesturesList.innerHTML = '<div class="gesture-item">No custom gestures available</div>';
            }
        } catch (error) {
            console.error('Failed to load gestures list:', error);
            const gesturesList = document.getElementById('gestures-list');
            gesturesList.innerHTML = '<div class="gesture-item">Error loading gestures</div>';
        }
    }

    setupEventListeners() {
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        
        startBtn.addEventListener('click', () => this.startCamera());
        stopBtn.addEventListener('click', () => this.stopCamera());
    }

    initializeMediaPipe() {
        this.holistic = new Holistic({
            locateFile: (file) => {
                return `https://cdn.jsdelivr.net/npm/@mediapipe/holistic/${file}`;
            }
        });

        this.holistic.setOptions({
            modelComplexity: 1,
            smoothLandmarks: true,
            enableSegmentation: false,
            smoothSegmentation: true,
            refineFaceLandmarks: true, // Enable face landmark refinement
            minDetectionConfidence: 0.7, // Increase for better detection
            minTrackingConfidence: 0.7  // Increase for better tracking
        });

        this.holistic.onResults((results) => this.onResults(results));
    }

    async startCamera() {
        try {
            const constraints = {
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'user'
                }
            };

            const stream = await navigator.mediaDevices.getUserMedia(constraints);
            this.webcamElement.srcObject = stream;

            // Wait for video to load metadata to get actual dimensions
            await new Promise((resolve) => {
                this.webcamElement.addEventListener('loadedmetadata', resolve, { once: true });
            });

            this.camera = new Camera(this.webcamElement, {
                onFrame: async () => {
                    await this.holistic.send({ image: this.webcamElement });
                },
                width: 640,
                height: 480
            });

            await this.camera.start();
            
            this.isRunning = true;
            this.frameData = [];
            this.frameCount = 0;
            this.startTime = Date.now();
            
            document.getElementById('startBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;
            
            console.log('Camera started successfully');
        } catch (error) {
            console.error('Error starting camera:', error);
            alert('Error starting camera. Please check your camera permissions.');
        }
    }

    stopCamera() {
        if (this.camera) {
            this.camera.stop();
        }
        
        if (this.webcamElement.srcObject) {
            const tracks = this.webcamElement.srcObject.getTracks();
            tracks.forEach(track => track.stop());
            this.webcamElement.srcObject = null;
        }
        
        this.isRunning = false;
        this.frameData = [];
        
        document.getElementById('startBtn').disabled = false;
        document.getElementById('stopBtn').disabled = true;
        
        // Clear canvas
        this.canvasCtx.clearRect(0, 0, this.canvasElement.width, this.canvasElement.height);
        
        console.log('Camera stopped');
    }

    onResults(results) {
        if (!this.isRunning) return;

        // Wait for video to have valid dimensions
        if (!this.webcamElement.videoWidth || !this.webcamElement.videoHeight) {
            return;
        }

        // Get the actual dimensions of the video element
        const videoRect = this.webcamElement.getBoundingClientRect();
        const videoWidth = this.webcamElement.videoWidth;
        const videoHeight = this.webcamElement.videoHeight;
        
        // Ensure canvas has proper dimensions
        if (this.canvasElement.width !== Math.floor(videoRect.width) || 
            this.canvasElement.height !== Math.floor(videoRect.height)) {
            this.canvasElement.width = Math.floor(videoRect.width);
            this.canvasElement.height = Math.floor(videoRect.height);
        }

        // Clear canvas with proper dimensions
        this.canvasCtx.clearRect(0, 0, this.canvasElement.width, this.canvasElement.height);

        // Save canvas state
        this.canvasCtx.save();

        // Calculate proper scaling with aspect ratio preservation
        const scaleX = this.canvasElement.width / videoWidth;
        const scaleY = this.canvasElement.height / videoHeight;
        
        // Apply scaling transformation
        this.canvasCtx.scale(scaleX, scaleY);

        // Draw landmarks with synchronized scaling
        this.drawLandmarks(results, videoWidth, videoHeight);

        // Restore canvas state
        this.canvasCtx.restore();

        // Collect frame data
        this.collectFrameData(results);

        // Process prediction every 30 frames but with smart timing
        if (this.frameData.length >= 30) {
            this.processPrediction();
        }
    }

    drawLandmarks(results, videoWidth, videoHeight) {
        // Draw pose landmarks with enhanced visibility
        if (results.poseLandmarks) {
            drawConnectors(this.canvasCtx, results.poseLandmarks, POSE_CONNECTIONS, {
                color: '#00FF00', 
                lineWidth: 4
            });
            drawLandmarks(this.canvasCtx, results.poseLandmarks, {
                color: '#FF0000', 
                lineWidth: 2,
                radius: 5
            });
        }

        // Draw hand landmarks with enhanced visibility
        if (results.leftHandLandmarks) {
            drawConnectors(this.canvasCtx, results.leftHandLandmarks, HAND_CONNECTIONS, {
                color: '#CC0000', 
                lineWidth: 4
            });
            drawLandmarks(this.canvasCtx, results.leftHandLandmarks, {
                color: '#00FFFF', 
                lineWidth: 2,
                radius: 4
            });
        }

        if (results.rightHandLandmarks) {
            drawConnectors(this.canvasCtx, results.rightHandLandmarks, HAND_CONNECTIONS, {
                color: '#0000CC', 
                lineWidth: 4
            });
            drawLandmarks(this.canvasCtx, results.rightHandLandmarks, {
                color: '#FFFF00', 
                lineWidth: 2,
                radius: 4
            });
        }

        // Draw face landmarks with enhanced visibility and individual points
        if (results.faceLandmarks) {
            // Draw face oval outline
            drawConnectors(this.canvasCtx, results.faceLandmarks, FACEMESH_FACE_OVAL, {
                color: '#00CCCC', 
                lineWidth: 2
            });
            
            // Draw key face landmarks for better tracking
            drawLandmarks(this.canvasCtx, results.faceLandmarks, {
                color: '#FF00FF',
                lineWidth: 1,
                radius: 1
            });
        }
    }

    collectFrameData(results) {
        const currentTime = Date.now();
        const timeInSeconds = (currentTime - this.startTime) / 1000;

        const frameData = {
            timeInSeconds: timeInSeconds,
            frameNumber: this.frameCount++,
            poseLandmarks: results.poseLandmarks || null,
            faceLandmarks: results.faceLandmarks || null,
            leftHandLandmarks: results.leftHandLandmarks || null,
            rightHandLandmarks: results.rightHandLandmarks || null
        };

        this.frameData.push(frameData);

        // Keep only last 30 frames
        if (this.frameData.length > 30) {
            this.frameData.shift();
        }
    }

    async processPrediction() {
        if (this.frameData.length === 0) return;

        try {
            const response = await fetch(`${this.serverUrl}/predict`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(this.frameData)
            });

            const result = await response.json();
            
            // Skip silent predictions (no gesture detected states)
            if (result.silent) {
                return; // Don't process or display silent predictions
            }
            
            // Only display meaningful predictions with reasonable confidence
            if (result.gesture && 
                result.gesture !== 'no_gesture_detected' && 
                result.confidence > 0.6) {
                
                this.displayPrediction(result);
                console.log('✅ Gesture detected:', result.gesture, 'Confidence:', result.confidence.toFixed(3));
                
            } else if (result.reason && 
                      !['rate_limited', 'in_rest_state', 'insufficient_data'].includes(result.reason)) {
                
                // Show meaningful status updates (but not spam)
                console.log('🎯 Status:', result.reason);
            }

        } catch (error) {
            console.error('Prediction error:', error);
            this.displayError('Prediction failed');
        }
    }

    displayPrediction(result) {
        const predictionElement = document.getElementById('prediction');
        const confidenceElement = document.getElementById('confidence');
        const modelUsedElement = document.getElementById('model-used');

        if (result.error) {
            predictionElement.textContent = 'Error';
            confidenceElement.textContent = result.error;
            modelUsedElement.textContent = '';
            return;
        }

        // Handle both 'gesture' and 'sign_name' fields for compatibility
        const gesture = result.gesture || result.sign_name;
        
        if (gesture && gesture !== 'unknown' && gesture !== 'no_gesture_detected') {
            predictionElement.textContent = gesture.toUpperCase();
            confidenceElement.textContent = `Confidence: ${(result.confidence * 100).toFixed(1)}%`;
            modelUsedElement.textContent = `Model: ${result.model_used || 'Unknown'}`;
            
            // Add visual feedback with animation
            predictionElement.style.animation = 'none';
            predictionElement.offsetHeight; // Trigger reflow
            predictionElement.style.animation = 'pulse 0.5s ease-in-out';
            
            // Auto-clear after 3 seconds
            setTimeout(() => {
                if (predictionElement.textContent === gesture.toUpperCase()) {
                    predictionElement.textContent = 'Ready for gesture...';
                    confidenceElement.textContent = '';
                    modelUsedElement.textContent = '';
                }
            }, 3000);
        } else {
            predictionElement.textContent = 'Ready for gesture...';
            confidenceElement.textContent = '';
            modelUsedElement.textContent = '';
        }
    }

    displayError(message) {
        const predictionElement = document.getElementById('prediction');
        const confidenceElement = document.getElementById('confidence');
        const modelUsedElement = document.getElementById('model-used');

        predictionElement.textContent = 'Error';
        confidenceElement.textContent = message;
        modelUsedElement.textContent = '';
    }
}

// Initialize the app when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new CustomGesturesApp();
});
