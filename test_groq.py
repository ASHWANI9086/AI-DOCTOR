"""Quick test: find which Groq vision models work and what the error is."""
import os, base64
from dotenv import load_dotenv
load_dotenv()

from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

# Use a tiny bundled test image (redeye.jpg)
IMAGE_PATH = "redeye.jpg"
with open(IMAGE_PATH, "rb") as f:
    encoded = base64.b64encode(f.read()).decode("utf-8")

QUERY = "What do you see in this image? Describe it briefly."

models = [
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "llama-3.2-90b-vision-preview",
    "llama-3.2-11b-vision-preview",
]

for model in models:
    print(f"\n{'='*60}")
    print(f"Testing model: {model}")
    try:
        resp = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": QUERY},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}},
                    ],
                }
            ],
            model=model,
            max_tokens=256,
        )
        content = resp.choices[0].message.content
        print(f"SUCCESS! Response: {content[:200]}")
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")

print("\n\nAlso listing available models from API:")
try:
    models_list = client.models.list()
    for m in models_list.data:
        print(f"  - {m.id}")
except Exception as e:
    print(f"Could not list models: {e}")
