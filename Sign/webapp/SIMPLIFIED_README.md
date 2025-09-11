# Simplified Sign Language Recognition Project

## What Was Removed/Simplified

### ❌ Removed Features:
1. **ASL Dictionary** - No more video dictionary lookup
2. **ASL Video Playing** - Removed video playback functionality 
3. **API Configuration Settings** - Removed complex API settings
4. **Particles Background** - Removed animated background particles
5. **Complex Modal System** - Removed settings and dictionary modals
6. **Docker Configuration** - Simplified to run directly with Python
7. **Complex Styling** - Simplified to clean, minimal UI
8. **tf-utils Dependency** - Removed problematic GitHub dependency

### ✅ What Remains (Core Features):
1. **Camera Access** - Enable webcam for real-time detection
2. **Sign Language Recognition** - Predict ASL signs from hand/body movements
3. **Sentence Generation** - Convert predicted signs into coherent sentences
4. **Real-time Landmark Detection** - MediaPipe for extracting landmarks
5. **Clean UI** - Simple, responsive interface

## Training Data Information

Based on the evaluation.txt file, this model was trained on **250 different ASL signs** with the following distribution:

- **Average samples per sign**: ~300-400 videos
- **Total dataset size**: ~94,477 videos across 250 signs
- **Model accuracy**: 92% overall accuracy
- **Signs range from**: Common words like "hello", "water", "food" to complex phrases

### Sample signs included:
- Basic words: hello, yes, no, water, food, car, book
- Actions: walk, run, jump, dance, eat, drink
- Objects: apple, balloon, flower, shirt, shoe
- Family: mom, dad, brother, sister, aunt, uncle
- Animals: cat, dog, bird, elephant, tiger, zebra
- Colors: red, blue, green, yellow, black, white
- And many more...

## How to Run the Simplified Project

### 1. Prerequisites
- Python 3.8+ installed
- Webcam/camera access

### 2. Installation
```bash
# Navigate to the webapp directory
cd d:\MAJOR-PROJECT\Sign\webapp

# Install dependencies (simplified version)
pip install -r requirements_simple.txt
```

### 3. Optional: Set up Google API for Sentence Generation
```bash
# Copy the environment template
copy .env.example .env

# Edit .env file and add your Google API key
GOOGLE_API_KEY=your_actual_api_key_here
```

### 4. Run the Application
```bash
# Start the server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 5. Access the Application
Open your browser and go to: `http://127.0.0.1:8000`

## How to Use

1. **Click "Enable Camera"** - Grant camera permissions
2. **Position yourself** - Make sure your hands and upper body are visible
3. **Start signing** - Perform ASL signs clearly
4. **View predictions** - See real-time sign predictions in the "Current Sign" section
5. **Read sentences** - Generated sentences appear in the "Generated Sentence" section

## File Structure (Simplified)

```
webapp/
├── app/
│   └── main.py                    # Main FastAPI application
├── module/
│   ├── islr/
│   │   ├── model.py              # Sign recognition model
│   │   ├── model.tflite          # TensorFlow Lite model
│   │   └── dict_sign.csv         # Sign dictionary
│   └── llm/
│       └── asl_sentence_generator.py  # Sentence generation
├── web/islr/
│   ├── index_simple.html         # Simplified HTML interface
│   ├── style_simple.css          # Clean, minimal styling
│   └── script_simple.js          # Core JavaScript functionality
├── requirements_simple.txt       # Simplified dependencies
└── .env.example                  # Environment template
```

## What Each File Does

- **main.py**: FastAPI server that handles web requests and serves the interface
- **model.py**: Contains the sign language recognition logic using TensorFlow
- **asl_sentence_generator.py**: Uses Google's Gemini AI to create sentences from signs
- **index_simple.html**: Clean web interface with camera and prediction display
- **script_simple.js**: Handles camera, MediaPipe landmarks, and API communication
- **style_simple.css**: Modern, responsive styling

## Benefits of Simplification

1. **Faster Setup** - No complex dependencies or Docker
2. **Easier to Understand** - Clean, focused codebase
3. **Better Performance** - Removed unnecessary features
4. **More Reliable** - Fewer potential points of failure
5. **Mobile Friendly** - Responsive design works on phones/tablets

## Tips for Best Results

1. **Good Lighting** - Ensure adequate lighting for camera
2. **Clear Background** - Plain background helps with detection
3. **Proper Distance** - Stay 2-3 feet from camera
4. **Clear Gestures** - Make distinct, deliberate sign movements
5. **Pause Between Signs** - Give the model time to process each sign

The simplified version focuses on the core functionality while removing all the extra features that weren't essential for basic sign language recognition!
