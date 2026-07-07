import os
import base64
import mimetypes
from groq import Groq
from dotenv import load_dotenv
load_dotenv(override=True)


def encode_image(image_path):
    """Encode a local image file to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def get_image_mime_type(image_path):
    """Detect the correct MIME type for an image file."""
    mime_type, _ = mimetypes.guess_type(image_path)
    if mime_type and mime_type.startswith("image/"):
        return mime_type
    with open(image_path, "rb") as f:
        header = f.read(12)
    if header[:8] == b'\x89PNG\r\n\x1a\n':
        return "image/png"
    elif header[:3] == b'\xff\xd8\xff':
        return "image/jpeg"
    elif header[:4] == b'RIFF' and header[8:12] == b'WEBP':
        return "image/webp"
    elif header[:6] in (b'GIF87a', b'GIF89a'):
        return "image/gif"
    return "image/jpeg"


DOCTOR_INSTRUCTIONS = (
    "You are a highly experienced and compassionate medical specialist with expertise in "
    "radiology, dermatology, and general medicine. "
    "Examine the image thoroughly and provide a precise diagnosis with accurate medical terminology. "
    "If you detect any abnormalities, describe the condition, symptoms, and severity in clear patient-friendly language. "
    "Provide multiple possible diagnoses (differential diagnoses) based on the visual clues, ranked by probability. "
    "Suggest detailed treatment options including prescription medications with dosage, home remedies, and preventive measures. "
    "If the condition appears serious, recommend consulting a specialist or seeking immediate medical attention. "
    "Structure your response in clear natural paragraphs starting with a direct diagnosis. "
    "Do not use markdown, bullet points, or special characters. "
    "Ensure your language is empathetic, reassuring, and easy to understand like a real doctor addressing a patient. "
    "Be concise and medically accurate but offer practical and actionable advice. "
    "Conclude with a comforting note or next steps."
)


def analyze_image_with_query(query, encoded_image, image_path=None,
                              model="meta-llama/llama-4-scout-17b-16e-instruct"):
    """Send an image + text query to the Groq vision model and return the response.
    
    IMPORTANT: The system role is intentionally NOT used here because llama-4-scout
    returns empty content when a system message is combined with image input.
    All instructions are embedded in the user message instead.
    """
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    client = Groq(api_key=GROQ_API_KEY)

    mime_type = get_image_mime_type(image_path) if image_path else "image/jpeg"

    # Combine instructions + patient query into a single user message
    # (system role causes empty output with vision models on Groq)
    full_user_text = DOCTOR_INSTRUCTIONS + "\n\nPatient's concern: " + query

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": full_user_text
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{encoded_image}",
                    },
                },
            ],
        }
    ]

    models_to_try = [model, "meta-llama/llama-4-scout-17b-16e-instruct"]
    # Deduplicate while preserving order
    seen = set()
    models_to_try = [m for m in models_to_try if not (m in seen or seen.add(m))]

    last_error = None
    for m in models_to_try:
        try:
            chat_completion = client.chat.completions.create(
                messages=messages,
                model=m,
                max_tokens=1024,
                temperature=0.7,
            )
            response_text = chat_completion.choices[0].message.content
            if response_text and response_text.strip():
                print(f"[brain] Got response from model: {m}")
                return response_text
            else:
                print(f"[brain] Model {m} returned empty content, trying next...")
        except Exception as e:
            last_error = e
            print(f"[brain] Model {m} failed: {e}")
            continue

    raise Exception(f"Vision model failed. Error: {last_error}")
