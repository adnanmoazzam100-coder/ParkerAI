import asyncio
import edge_tts
import pygame
import tempfile
import os
import time

pygame.mixer.init()

# The top 4 candidates for the "Parker/Jarvis" persona
voice_candidates = [
    {"name": "Thomas (Crisp British)", "id": "en-GB-ThomasNeural"},
    {"name": "Ryan (Smooth British)", "id": "en-GB-RyanNeural"},
    {"name": "Christopher (Deep American)", "id": "en-US-ChristopherNeural"},
    {"name": "William (Sharp Australian)", "id": "en-AU-WilliamNeural"}
]

test_phrase = "Good evening, sir. I have run the diagnostics. The system is perfectly fine, though I cannot speak for your sleeping habits."

async def test_voices():
    print("\n--- INITIATING PARKER VOICE AUDITIONS ---\n")
    
    for voice in voice_candidates:
        print(f"Auditioning: {voice['name']} ({voice['id']})")
        
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                temp_path = f.name
                
            # Using +10% rate to give it that fast, efficient Jarvis cadence
            communicate = edge_tts.Communicate(test_phrase, voice['id'], rate="+10%")
            await communicate.save(temp_path)
            
            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
            pygame.mixer.music.unload()
            os.remove(temp_path)
            
            # Brief pause between auditions
            time.sleep(1.5) 
            
        except Exception as e:
            print(f"Failed to play {voice['name']}: {e}")

    print("\n--- AUDITIONS COMPLETE ---")

# Run the test
asyncio.run(test_voices())