# voiceBot UI with Gradio
import os
import sys
import traceback
from dotenv import load_dotenv
load_dotenv(override=True)

import gradio as gr

from brain_of_the_doctor import encode_image, analyze_image_with_query, get_image_mime_type
from voice_of_the_patient import transcribe_with_groq
from voice_of_the_doctor import text_to_speech_with_gtts

# Use /tmp for audio output — always writable in Docker (Render, HuggingFace, etc.)
AUDIO_OUTPUT_PATH = "/tmp/final.mp3"
DEBUG_LOG = "/tmp/debug.log"


def log(msg):
    """Write debug message to both console and file."""
    print(msg, flush=True)
    try:
        with open(DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass


def process_inputs(audio_filepath, text_input, image_filepath):
    try:
        log(f"\n{'='*60}")
        log(f"[INPUTS] audio={audio_filepath} | text='{text_input}' | image={image_filepath}")

        patient_query = ""

        # Step 1: Transcribe audio if provided
        if audio_filepath and os.path.exists(audio_filepath):
            log("[STEP1] Transcribing audio...")
            try:
                transcribed = transcribe_with_groq(
                    GROQ_API_KEY=os.environ.get("GROQ_API_KEY"),
                    audio_filepath=audio_filepath,
                    stt_model="whisper-large-v3"
                )
                log(f"[STEP1] Transcription OK: '{transcribed}'")
                patient_query = transcribed or ""
            except Exception as e:
                log(f"[STEP1] Transcription error: {type(e).__name__}: {e}")
                patient_query = ""

        # Append or use typed text
        if text_input and str(text_input).strip():
            if patient_query:
                patient_query = patient_query + " " + str(text_input).strip()
            else:
                patient_query = str(text_input).strip()

        # Fallback default query
        if not patient_query:
            patient_query = "Please analyze this medical image and provide a detailed diagnosis, possible conditions, and recommended treatment."

        log(f"[STEP1] Final query: '{patient_query[:100]}'")

        # Step 2: Analyze image or use text-only
        doctor_response = ""
        if image_filepath and os.path.exists(str(image_filepath)):
            log(f"[STEP2] Analyzing image: {image_filepath}")
            try:
                doctor_response = analyze_image_with_query(
                    query=patient_query,
                    encoded_image=encode_image(image_filepath),
                    image_path=image_filepath,
                    model="meta-llama/llama-4-scout-17b-16e-instruct"
                )
                log(f"[STEP2] Analysis OK: '{doctor_response[:80]}'")
            except Exception as e:
                log(f"[STEP2] Analysis error: {type(e).__name__}: {e}")
                log(traceback.format_exc())
                doctor_response = f"Sorry, could not analyze the image. ({type(e).__name__}: {e})"
        else:
            log("[STEP2] No image — text-only response")
            try:
                from groq import Groq
                client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
                resp = client.chat.completions.create(
                    messages=[{"role": "user", "content": (
                        "You are a compassionate medical specialist. Answer the following patient concern "
                        "clearly and helpfully. Do not use markdown. Speak like a doctor to a patient.\n\n"
                        f"Patient says: {patient_query}"
                    )}],
                    model="llama-3.3-70b-versatile",
                    max_tokens=1024,
                )
                doctor_response = resp.choices[0].message.content
                log(f"[STEP2] Text-only OK: '{doctor_response[:80]}'")
            except Exception as e:
                log(f"[STEP2] Text-only error: {type(e).__name__}: {e}")
                doctor_response = f"Sorry, could not process your request. ({type(e).__name__}: {e})"

        # Step 3: Text-to-speech (best-effort, don't fail the whole response)
        output_audio = None
        try:
            text_to_speech_with_gtts(input_text=doctor_response, output_filepath=AUDIO_OUTPUT_PATH)
            if os.path.exists(AUDIO_OUTPUT_PATH):
                output_audio = AUDIO_OUTPUT_PATH
                log(f"[STEP3] TTS OK: {output_audio}")
            else:
                log("[STEP3] TTS file not created")
        except Exception as e:
            log(f"[STEP3] TTS error: {type(e).__name__}: {e}")
            output_audio = None

        log(f"[DONE] Returning results. audio={output_audio}")
        return patient_query, doctor_response, output_audio

    except BaseException as e:
        err = traceback.format_exc()
        log(f"[FATAL] Unhandled exception in process_inputs:\n{err}")
        return f"Error: {str(e)}", f"An unexpected error occurred: {str(e)}", None


# Gradio Interface
iface = gr.Interface(
    fn=process_inputs,
    inputs=[
        gr.Audio(
            sources=["microphone", "upload"],
            type="filepath",
            label="🎤 Option 1: Record or Upload Voice (optional)"
        ),
        gr.Textbox(
            lines=3,
            placeholder="Type your symptoms here... e.g. 'I have a red rash on my arm that itches'",
            label="✍️ Option 2: Type Your Symptoms (optional)"
        ),
        gr.Image(
            type="filepath",
            label="🖼️ Upload Medical Image (skin, X-ray, eye, dental, etc.)"
        )
    ],
    outputs=[
        gr.Textbox(label="📝 Patient Query (your transcribed/typed symptoms)"),
        gr.Textbox(label="🩺 Doctor's Diagnosis & Advice", lines=10),
        gr.Audio(label="🔊 Doctor's Voice Response", type="filepath")
    ],
    title="🩺 VisionaryCare — AI Doctor That Sees & Speaks for Your Health",
    description=(
        "**How to use:** Upload a medical image AND either speak your symptoms or type them. "
        "Both voice and text are optional — you can also just upload an image for analysis. "
        "The AI doctor will provide a detailed diagnosis spoken aloud!"
    )
)

# Render.com injects PORT env var dynamically — must use it or the service won't bind
_port = int(os.environ.get("PORT", os.environ.get("GRADIO_SERVER_PORT", "7860")))
_host = os.environ.get("GRADIO_SERVER_NAME", "0.0.0.0")

print(f"[startup] Launching Gradio on {_host}:{_port}", flush=True)

iface.launch(
    server_name=_host,
    server_port=_port,
    share=False,
    debug=False,
    theme=gr.themes.Soft(),
    allowed_paths=["/app", ".", "/tmp"],   # allow Gradio to serve audio from /tmp
    show_error=True,
)
