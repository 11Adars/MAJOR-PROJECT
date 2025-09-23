from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import module.islr.model as model
import os
from fastapi import HTTPException
import smtplib
from email.message import EmailMessage

def load_env_file():
    """Lightweight .env loader (avoids extra dependency). Sets vars only if absent."""
    try:
        env_path = Path(__file__).resolve().parent.parent / ".env"  # webapp/.env
        if not env_path.exists():
            return
        with env_path.open("r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:  # do not override existing environment
                    os.environ[k] = v
    except Exception as e:
        print(f"[ENV] Warning: unable to load .env file: {e}")

# Load .env before app / model init so endpoints can read vars
load_env_file()

# Initialize the FastAPI app
app = FastAPI()
model = model.IsolatedASLRecognition(model_path="module/islr")

# Set up CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust origins for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define Pydantic models for data validation
class Landmark(BaseModel):
    x: float
    y: float
    z: Optional[float] = None
    visibility: Optional[float] = None

class LandmarkData(BaseModel):
    timeInSeconds: float
    frameNumber: int
    poseLandmarks: Optional[List[Landmark]] = None
    faceLandmarks: Optional[List[Landmark]] = None
    leftHandLandmarks: Optional[List[Landmark]] = None
    rightHandLandmarks: Optional[List[Landmark]] = None

# Serve static files (CSS and JS) from the "web" folder
app.mount("/web/islr", StaticFiles(directory="web/islr"), name="web_islr")

# Serve the main HTML page
@app.get("/")
async def read_root():
    return FileResponse(Path("web/islr/index.html"))

# Prediction endpoint
@app.post("/islr/predict")
async def predict(data: List[LandmarkData]):  # Corrected the type annotation
    result = model.predict(data)
    return result

@app.post("/islr/reset")
async def reset_state():
    model.reset()
    return {"status": 200, "message": "State reset"}

@app.post("/islr/send")
async def send_sentence():
    sentence = model.pred_sentence or ""
    if not sentence:
        return {"status": 400, "message": "No sentence to send"}

    to_addr = (os.getenv("PREDICTION_EMAIL_TO", "example@domain.com") or "").strip()
    smtp_host = (os.getenv("SMTP_HOST") or "").strip()
    smtp_port = int((os.getenv("SMTP_PORT", "587") or "587").strip())
    smtp_user = (os.getenv("SMTP_USER") or "").strip()
    smtp_pass = (os.getenv("SMTP_PASS") or "").strip()
    debug_mode = os.getenv("SMTP_DEBUG", "false").lower() == "true"

    missing = [k for k,v in {"SMTP_HOST":smtp_host,"SMTP_USER":smtp_user,"SMTP_PASS":smtp_pass}.items() if not v]
    if missing:
        return {"status": 500, "message": f"Missing config: {', '.join(missing)}"}

    msg = EmailMessage()
    msg["Subject"] = "Sign Recognition Sentence"
    msg["From"] = smtp_user
    msg["To"] = to_addr
    msg.set_content(f"Recognized sentence:\n{sentence}")

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
            code, hello = server.ehlo()
            if debug_mode: print("EHLO", code, hello)
            server.starttls()
            code, tls = server.ehlo()
            if debug_mode: print("Post-TLS EHLO", code, tls)
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return {"status": 200, "message": "Email sent"}
    except smtplib.SMTPAuthenticationError as e:
        return {"status": 401, "message": "Authentication failed (check app password / account security)", "detail": str(e)}
    except (smtplib.SMTPConnectError, TimeoutError) as e:
        return {"status": 502, "message": "SMTP connection failed", "detail": str(e)}
    except OSError as e:  # DNS resolution or socket error
        return {"status": 502, "message": "Network/DNS error when connecting to SMTP host", "detail": str(e)}
    except smtplib.SMTPRecipientsRefused as e:
        return {"status": 400, "message": "Recipient refused", "detail": str(e)}
    except smtplib.SMTPException as e:
        return {"status": 500, "message": "SMTP error", "detail": str(e)}
    except Exception as e:
        return {"status": 500, "message": "Unexpected error", "detail": str(e)}

# Run the app with Uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)