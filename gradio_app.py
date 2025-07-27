# voiceBot UI with Gradio
import os
import gradio as gr

from brain_of_the_doctor  import encode_image, analyze_image_with_query
from voice_of_the_patient import record_audio, transcribe_with_groq
from voice_of_the_doctor import text_to_speech_with_gtts

system_prompt="""You are a highly experienced and compassionate medical specialist with expertise in radiology, dermatology, and general medicine.  
            Examine the image thoroughly and provide a **precise diagnosis** with accurate medical terminology.  
            If you detect any abnormalities, describe the **condition, symptoms, and severity** in clear, patient-friendly language.  
            Provide **multiple possible diagnoses** (differential diagnoses) based on the visual clues, ranked by probability.  
            Suggest detailed **treatment options**, including:
            - **Prescription medications** (generic and brand names), dosage, and duration.  
            - **Home remedies** and lifestyle adjustments.  
            - **Preventive measures** to avoid further complications.  
            Mention potential **side effects or interactions** of the prescribed medication if relevant.  
            If the condition appears serious, **recommend consulting a specialist** or seeking immediate medical attention.  
            Structure your response in **clear, natural paragraphs**, starting with a direct diagnosis.  
            **Avoid using markdown, bullet points, or special characters.**  
            Ensure your language is **empathetic, reassuring, and easy to understand**, mimicking a real doctor addressing a patient.  
            **Be concise and medically accurate**, but offer practical and actionable advice.  
            Conclude with a comforting note or next steps (e.g., "If symptoms persist, consult your healthcare provider."). """ 

def process_inputs(audio_filepath, image_filepath):
    speech_to_text_output = transcribe_with_groq(GROQ_API_KEY=os.environ.get("GROQ_API_KEY"), 
                                                 audio_filepath=audio_filepath,
                                                 stt_model="whisper-large-v3")

    # Handle the image input
    if image_filepath:
        doctor_response = analyze_image_with_query(query=system_prompt+speech_to_text_output, encoded_image=encode_image(image_filepath), model="meta-llama/llama-4-scout-17b-16e-instruct")      #model="llama-3.2-11b-vision-preview")
    else:
        doctor_response = "No image provided for me to analyze"

    voice_of_doctor = text_to_speech_with_gtts(input_text=doctor_response, output_filepath="final.mp3") 

    return speech_to_text_output, doctor_response, voice_of_doctor


# Create the interface
iface = gr.Interface(
    fn=process_inputs,
    inputs=[
        gr.Audio(sources=["microphone"], type="filepath"),
        gr.Image(type="filepath")
    ],
    outputs=[
        gr.Textbox(label="Speech to Text"),
        gr.Textbox(label="Doctor's Response"),
        gr.Audio("Temp.mp3")
    ],
    title="VisionaryCare → World's First AI That Sees & Speaks for Your Health"
)

iface.launch(share=True, debug=True)

