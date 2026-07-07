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
    "Examine the provided image carefully and give a structured medical report divided into the following clearly labeled sections. "
    "Use the exact section headers listed below. Each section must be on its own line with a blank line before it. "
    "Use simple numbered or dashed lists inside each section — NOT paragraphs. "
    "Keep language empathetic, clear, and easy for a non-medical patient to understand.\n\n"

    "Use EXACTLY this structure:\n\n"

    "DIAGNOSIS\n"
    "State the most likely diagnosis in 1-2 sentences.\n\n"

    "DIFFERENTIAL DIAGNOSES\n"
    "List 2-4 possible conditions ranked by probability (e.g. 1. Condition — 80%).\n\n"

    "SYMPTOMS TO WATCH\n"
    "List the key symptoms the patient may be experiencing or should watch for.\n\n"

    "SEVERITY\n"
    "State whether the condition is Minor / Moderate / Severe and explain briefly.\n\n"

    "TREATMENT STEPS\n"
    "List step-by-step immediate home care or clinical treatment actions.\n\n"

    "RECOMMENDED MEDICINES\n"
    "List medicines with name, type (OTC or prescription), and dosage guidance. "
    "Always add: 'Consult a doctor before taking any medication.'\n\n"

    "PRECAUTIONS\n"
    "List important dos and don'ts to avoid worsening the condition.\n\n"

    "WHEN TO SEE A DOCTOR IMMEDIATELY\n"
    "List specific warning signs that require urgent medical attention.\n\n"

    "RECOVERY TIPS\n"
    "List 2-3 practical tips for faster recovery and prevention in future.\n\n"

    "End with one short, warm, reassuring sentence addressed to the patient."
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
