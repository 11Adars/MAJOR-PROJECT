ISLR Model API Deployment Guide
This guide explains how to deploy the Model API for the ISLR project using docker implementation.

Folder Structure
Your project directory should have the following structure:

app/
├── dict_sign.csv                       # Supporting data file
├── main.py                             # FastAPI application
├── model.tflite                        # Model file

module/
├── islr/      
|   ├── dict_sign.csv                   # Supporting data file   
|   ├── main.py                         # FastAPI application
|   ├── model.tflite                    # Model file
├── llm/               
|   ├── asl_sentence_generator.py       # Model file

web/islr/
├── videos/                             # ASL Sign Videos
├── index.html                          # Frontend HTML file
├── particles.js                        # JavaScript for background design
├── script.js                           # JavaScript for frontend logic
├── style.css                           # CSS for styling
Dockerfile                              # Docker configuration (optional)
requirements.txt                        # Python dependencies

Prerequisites
Before deploying the API, ensure the following requirements are met:

Python 3.8+:
Install Python from python.org.

Install Dependencies:
Install required Python libraries by running:

pip install -r requirements.txt
This will install dependencies such as FastAPI and Uvicorn.

Running the API
To start the API server, follow these steps:

Navigate to the Project Directory:
Open your terminal and move to the ISLR project folder:

cd /path/to/ISLR
Run the API Using Uvicorn:
Execute the following command to start the server:

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
app.main:app refers to the FastAPI app located in main.py inside the app directory.
--host 0.0.0.0 makes the API accessible from external devices.
--port 8000 sets the port number to 8000.
--reload enables automatic reloading during development.
Access the API:
Once the server is running, you can access the API locally at:

http://127.0.0.1:8000