import google.generativeai as genai
from typing import List
from dotenv import load_dotenv
import os
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"  # adjust if needed
load_dotenv(dotenv_path=ENV_PATH)


# Generate a coherent English sentence from recognized ASL words
def generate_sentence(recognised_words: List[str]) -> str:
    """Use the Generative AI model to construct a coherent English sentence."""
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=GOOGLE_API_KEY)
    
    model = genai.GenerativeModel('gemini-pro')
    prompt = f"""
        Objective: Rearrange ASL-recognized words to form a simple, meaningful English sentence.
        Input: recognised_words = {' '.join(recognised_words)}
        Output: Provide a concise English sentence.
    """
    response = model.generate_content(prompt)

    return response.text