# Sign Language Recognition

#### Project Status: In Progress

## Project Intro/Objective

This project is part of my Master's Degree final project and focuses on an end-to-end system for isolated sign language recognition, featuring data preprocessing, deep learning-based model training, real-time prediction, and a web interface for live sign recognition to enhance accessibility and communication.

## Methods Used
- Real-Time Video Processing: Leveraging Mediapipe to extract landmarks from user-recorded videos for detecting hand and body positions relevant to American Sign Language (ASL) gestures.
- ASL Word Prediction: Using a Transformer model hosted in a Dockerized Python backend via FastAPI to predict the ASL word from the extracted landmarks.
- Sentence Generation: Utilizing a Large Language Model (Gemini LLM) to convert predicted ASL words into coherent sentences.
- Frontend Interaction: HTML, CSS, and JavaScript to create a user interface allowing video recording, visualization of extracted landmarks, and ASL video playback.

## Technologies
- Python
- MediaPipe
- TensorFlow (Transformer Model)
- FastAPI
- Docker
- HTML, CSS, JavaScript
- Gemini LLM
Render (for hosting the backend)

## Project Description

This project focuses on real-time sign language recognition using a combination of frontend and backend technologies. The following steps are implemented:

1. Landmark Extraction: Leveraging MediaPipe to extract hand and body landmarks from user-recorded ASL videos. This step involves real-time video processing to capture key features of ASL gestures.
2. ASL Word Prediction: Implementing a Transformer model in a Dockerized Python backend, served via FastAPI. The model processes the extracted landmarks to predict corresponding ASL words.
3. Sentence Generation: Using the Gemini LLM to convert the predicted ASL words into coherent sentences, enhancing communication for users.
4. User Interaction: Developing an intuitive web interface with HTML, CSS, and JavaScript to allow users to record videos, visualize extracted landmarks, and interact with ASL video playback.
5. Hosting and Deployment: The backend, including the model and API, is hosted on Render for seamless access and interaction.

## Dataset
The dataset used in this project is the **SignData Gatech**, which can be accessed at [SignData](https://signdata.cc.gatech.edu/).

## Directory Structure
```
├── model.ipynb        <- Jupyter Notebook containing the code for dataset preparation, model training, and evaluation.
├── README.md          <- Project documentation and instructions.
```

## Quick Links
- [SignData](https://signdata.cc.gatech.edu/)

## Requirements

The following packages and versions are required to run the project:

### Core Requirements
- Python 3.7.10

### Additional Requirements for Dataset Preparation
- Pandas 1.1.5

## Results

### Covid Model (Positive/Negative)
| Metric       | Value |
|--------------|-------|
| Accuracy     | 92.00%|
| Precision    | 93.00%|
| Recall       | 92.00%|
| F1-Score     | 92.00%|

## Contributing Members

**Team Members**
* [Syachrul Qolbi Nur Septi](https://www.linkedin.com/in/syachrulqolbi)  
