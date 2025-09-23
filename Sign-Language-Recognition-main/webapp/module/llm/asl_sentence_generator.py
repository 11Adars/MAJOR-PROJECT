import os
from pathlib import Path
from typing import List

import google.generativeai as genai
from dotenv import load_dotenv


# Load environment variables (API key) from project root .env if present
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)


def _build_prompt(recognized_words: List[str]) -> str:
    words = [w for w in recognized_words if w and w.strip()]
    if not words:
        return (
            "You received an empty list of ASL tokens. Respond with an empty string (no words)."
        )
    joined = " ".join(words)
    return (
        "You are an assistant that converts a list of ASL gloss tokens into a simple, grammatically correct English sentence.\n"
        "Rules:\n"
        "- Only use the provided words; you may add minimal linking words (a, the, is, to, am, are, will) if required for grammar.\n"
        "- Keep the sentence concise (max 15 words).\n"
        "- Return ONLY the sentence. No explanations, no quotes.\n"
        f"Tokens: {joined}\n"
        "Sentence:"
    )


# Generate a coherent English sentence from recognized ASL words
def generate_sentence(recognized_words: List[str]) -> str:
    """Turn recognized ASL gloss tokens into a simple English sentence via Gemini.

    Parameters:
        recognized_words: List of ASL-like tokens (e.g., ['I', 'GO', 'STORE']).
    Returns:
        A concise English sentence, or a fallback joined string if model call fails.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        # Fail fast with a clear message so caller can handle
        raise RuntimeError("GOOGLE_API_KEY not set in environment (.env)")

    genai.configure(api_key=api_key)

    # Model name may change; 'gemini-1.5-flash' is faster & cheaper for simple rewrites
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    model = genai.GenerativeModel(model_name)

    prompt = _build_prompt(recognized_words)

    try:
        response = model.generate_content(prompt)
    except Exception as e:
        # Log-like return (could integrate real logging if needed)
        return " ".join(recognized_words) if recognized_words else ""  # graceful fallback

    # Some SDK responses may have safety blocks or empty text
    text = getattr(response, "text", "") or "".join(getattr(response, "candidates", []) or [])
    text = (text or "").strip()
    if not text:
        return " ".join(recognized_words)

    # Simple post-cleanup: ensure single period at end (optional)
    if text and not text.endswith(('.', '!', '?')):
        text += '.'
    return text


if __name__ == "__main__":
    demo = ["I", "GO", "STORE", "TOMORROW"]
    print(generate_sentence(demo))