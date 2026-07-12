import asyncio
import edge_tts
import pygame
import tempfile
import os

pygame.mixer.init()

test_phrase = "Good evening, Boss. How does this voice sound to you? Am I the one?"

async def explore_voices():
    print("\n[Fetching the complete neural voice database...]")
    all_voices = await edge_tts.list_voices()
    
    # Filter for English voices (removes non-English languages to save you time)
    en_voices = [v for v in all_voices if v['Locale'].startswith('en-')]
    
    print(f"\nFound {len(en_voices)} English voices. Let's find the perfect one.")
    print("INSTRUCTIONS:")
    print("- Press ENTER to skip to the next voice.")
    print("- Type 'yes' and press ENTER to lock in the voice you like.")
    print("- Type 'quit' to stop.\n")
    
    for voice in en_voices:
        voice_id = voice['ShortName']
        gender = voice['Gender']
        locale = voice['Locale']
        
        print(f"Testing: {voice_id} | {gender} | {locale}")
        
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                temp_path = f.name
                
            # Playing at +10% speed for that snappy Jarvis cadence
            communicate = edge_tts.Communicate(test_phrase, voice_id, rate="+10%")
            await communicate.save(temp_path)
            
            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
                
            pygame.mixer.music.unload()
            os.remove(temp_path)
            
        except Exception as e:
            print(f" [Skipping {voice_id} due to playback error]")
            
        choice = input("Your choice (ENTER = Next | 'yes' = Select | 'quit' = Exit): ").strip().lower()
        
        if choice == 'yes' or choice == 'y':
            print("\n" + "="*50)
            print(f" [LOCKED IN] Your perfect voice is: {voice_id}")
            print("="*50)
            print(f"\nTo apply this to Parker, open core.py and change line 39 to:")
            print(f'current_voice_id = "{voice_id}"\n')
            break
        elif choice == 'quit' or choice == 'q':
            print("\nExiting the Explorer. See you, Boss.")
            break

if __name__ == "__main__":
    asyncio.run(explore_voices())