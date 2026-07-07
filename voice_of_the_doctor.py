# voice_of_the_doctor.py
# Text-to-Speech utilities for AI Doctor

import os
from gtts import gTTS


def text_to_speech_with_gtts(input_text, output_filepath):
    """Convert text to speech using gTTS and save to file. Returns the filepath."""
    language = "en"
    audioobj = gTTS(
        text=input_text,
        lang=language,
        slow=False
    )
    audioobj.save(output_filepath)
    return output_filepath


def text_to_speech_with_elevenlabs(input_text, output_filepath):
    """Convert text to speech using ElevenLabs API and save to file. Returns the filepath."""
    try:
        import elevenlabs
        from elevenlabs.client import ElevenLabs

        ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        audio = client.generate(
            text=input_text,
            voice="Aria",
            output_format="mp3_22050_32",
            model="eleven_turbo_v2"
        )
        elevenlabs.save(audio, output_filepath)
        return output_filepath

    except ImportError:
        print("ElevenLabs not installed. Falling back to gTTS.")
        return text_to_speech_with_gtts(input_text, output_filepath)