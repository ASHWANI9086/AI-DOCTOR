
🧠 AI Doctor – Project Setup Guide
This document walks you through setting up the development environment for the AI Doctor project. It covers the installation of system dependencies like FFmpeg and PortAudio, setting up a Python virtual environment, and running different phases of the application.

📁 Table of Contents
System Requirements

Install FFmpeg and PortAudio

macOS

Linux

Windows

Set Up Python Virtual Environment

Using Pipenv

Using pip + venv

Using Conda

Run the Application

Project Phases

✅ System Requirements
Python 3.10+

FFmpeg

PortAudio

Git

Pipenv / venv / Conda (any one)

Internet connection (for initial dependencies)

🔧 Install FFmpeg and PortAudio
macOS
Install Homebrew (if not installed):

bash
Copy
Edit
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
Install dependencies:

bash
Copy
Edit
brew install ffmpeg portaudio
Linux (Debian-based)
Update package list:

bash
Copy
Edit
sudo apt update
Install FFmpeg and PortAudio:

bash
Copy
Edit
sudo apt install ffmpeg portaudio19-dev
Windows
Download FFmpeg

Visit: https://ffmpeg.org/download.html

Download latest static build for Windows.

Extract and Add to PATH

Extract ZIP (e.g., to C:\ffmpeg)

Add C:\ffmpeg\bin to your system PATH.

Install PortAudio

Download from: http://files.portaudio.com/download.html

Install using installer or compile via MSVC if required.

📦 Set Up Python Virtual Environment
Option 1: Pipenv
Install Pipenv:

bash
Copy
Edit
pip install pipenv
Install dependencies:

bash
Copy
Edit
pipenv install
Activate environment:

bash
Copy
Edit
pipenv shell
Option 2: pip + venv
Create environment:

bash
Copy
Edit
python -m venv venv
Activate:

macOS/Linux:

bash
Copy
Edit
source venv/bin/activate
Windows:

bash
Copy
Edit
venv\Scripts\activate
Install packages:

bash
Copy
Edit
pip install -r requirements.txt
Option 3: Conda
Create Conda environment:

bash
Copy
Edit
conda create --name doctorai python=3.11
Activate:

bash
Copy
Edit
conda activate doctorai
Install dependencies:

bash
Copy
Edit
pip install -r requirements.txt
▶️ Run the Application
Make sure you are in the activated Python environment.

Step-by-step to run phases:
Phase	Command	Description
Brain of the Doctor	python brain_of_the_doctor.py	Core medical LLM & reasoning engine
Voice of Patient	python voice_of_the_patient.py	Captures patient input via voice
Voice of Doctor	python voice_of_the_doctor.py	Converts model output to speech
Gradio UI	python gradio_app.py	Web-based UI for interaction

🧩 Project Phases (Modular Flow)
Phase 1: Brain of the Doctor

Handles prompt engineering, LLM calls, and response formatting.

Phase 2: Voice of the Patient

Converts patient audio input to text using speech recognition.

Phase 3: Voice of the Doctor

Transforms text-based diagnosis to natural speech.

Phase 4: Gradio Interface

Brings everything together via an interactive UI.

