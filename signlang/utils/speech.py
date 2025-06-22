from gtts import gTTS
import pygame
from io import BytesIO
import time

def text_to_speech(text):
    """Convert text to speech and play it immediately"""
    try:
        # Initialize pygame mixer if not already initialized
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        # Create speech
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        
        # Play speech
        pygame.mixer.music.load(fp)
        pygame.mixer.music.play()
        
        # Wait for playback to finish
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
    except Exception as e:
        print(f"Error in text-to-speech: {str(e)}")