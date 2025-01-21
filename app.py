import os
from openai import OpenAI
from dotenv import load_dotenv
import streamlit as st
from audio_recorder_streamlit import audio_recorder

# Load API Key
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize OpenAI client
def setup_openai_client(api_key):
    try:
        return OpenAI(api_key=api_key)
    except Exception as e:
        st.error(f"Error setting up OpenAI client: {str(e)}")
        return None

# Transcribe audio to text
def transcribe_audio(client, audio_path):
    try:
        if client is None:
            raise ValueError("OpenAI client is not initialized")
        
        with open(audio_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            return response['text'] if 'text' in response else 'Transcription text not found'
    except Exception as e:
        st.error("Error transcribing audio.")
        return None

# Generate text-to-speech output
def generate_speech(client, text, audio_path):
    try:
        response = client.audio.speech.create(model="tts-1", voice="onyx", input=text)
        with open(audio_path, "wb") as audio_file:
            audio_file.write(response.content)
    except Exception as e:
        st.error(f"Error generating speech: {str(e)}")

# Auto-play the audio file
def play_audio(audio_file):
    try:
        with open(audio_file, "rb") as audio_file:
            audio_bytes = audio_file.read()
        base64_audio = base64.b64encode(audio_bytes).decode("utf-8")
        audio_html = f'<audio src="data:audio/mp3;base64,{base64_audio}" controls autoplay></audio>'
        st.markdown(audio_html, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error playing audio: {str(e)}")

# Fetch AI response
def fetch_ai_response(client, input_text):
    try:
        st.session_state.messages.append({"role": "user", "content": input_text})
        chat_completion = client.chat.completions.create(
            model="gpt-4",
            messages=st.session_state.messages
        )
        response = chat_completion.choices[0].message
        st.session_state.messages.append(response)
        return response.content
    except Exception as e:
        st.error(f"Error fetching AI response: {str(e)}")
        return "Sorry, I couldn't process your request."

# Main Voice Assistant Functionality
def main():
    st.title("Chef Mate: Voice Assistant")
    st.write("🎙️ Speak and let Chef Mate assist you in the kitchen!")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {'role': 'system', 'content': "You are Chef Mate, a voice assistant to help users with cooking."}
        ]

    # Initialize OpenAI Client
    client = setup_openai_client(OPENAI_API_KEY)
    if client is None:
        st.error("Failed to initialize OpenAI client. Check API key.")
        return

    # Record and Process Audio
    recorded_audio = audio_recorder()
    if recorded_audio:
        audio_file = "user_audio.mp3"
        with open(audio_file, "wb") as f:
            f.write(recorded_audio)

        transcribed_text = transcribe_audio(client, audio_file)
        if transcribed_text:
            st.write(f"**You said:** {transcribed_text}")
            st.session_state.messages.append({"role": "user", "content": transcribed_text})

            ai_response = fetch_ai_response(client, transcribed_text)
            response_audio = "response_audio.mp3"
            generate_speech(client, ai_response, response_audio)
            st.write(f"**Chef Mate says:** {ai_response}")
            play_audio(response_audio)

if __name__ == "__main__":
    main()
