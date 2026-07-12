import warnings
warnings.filterwarnings("ignore")
import os
import re
import sys
import json
import tempfile
import time as time_module
import threading
from datetime import datetime
import asyncio
import edge_tts
import pygame
import pyttsx3
import requests
import psutil
import msvcrt
import sounddevice as sd
import soundfile as sf
import numpy as np
from vosk import Model, KaldiRecognizer
from dotenv import load_dotenv
from groq import Groq
from ddgs import DDGS
from langdetect import detect

# --- INITIALISATION ---
print("Initialising the Grid...")
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY") 

if not GROQ_API_KEY:
    raise ValueError("Groq API Key not found! Please check your .env file.")

groq_client = Groq(api_key=GROQ_API_KEY)
try: 
    pygame.mixer.init()
except Exception as e: 
    print(f" [Warning: Audio mixer failed: {e}]")
    
# --- OFFLINE FAILSAFE UPGRADE (FEMALE VOICE) ---
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 175)
voices = tts_engine.getProperty('voices')
for voice in voices:
    if "zira" in voice.name.lower() or "female" in voice.name.lower():
        tts_engine.setProperty('voice', voice.id)
        break

ddgs = DDGS()
system_lock = threading.Lock()

# --- VOCAL MATRIX CONFIGURATION (F.R.I.D.A.Y. PROFILE) ---
current_voice_id = "en-IE-EmilyNeural"  
current_voice_rate = "+5%"              
current_voice_pitch = "+0Hz" 

def play_voice(text):
    global current_voice_rate, current_voice_id, current_voice_pitch
    if not text: return
    
    phonetics = {
        "Adnan": "Ahd-nahn",  
        "Groq": "Grock",
        "Tavily": "Tav-ill-ee",
        "LLM": "L L M",
        "API": "A P I"
    }
    
    for word, phonetic_spelling in phonetics.items():
        text = re.sub(r'\b' + re.escape(word) + r'\b', phonetic_spelling, text, flags=re.IGNORECASE)

    clean_speech = re.sub(r'[*_#\[\]\(\)\n]', ' ', text)
    clean_speech = re.sub(r'\s+', ' ', clean_speech).strip()
    
    if not clean_speech or len(clean_speech) < 2: return
    
    # --- AUTO-LANGUAGE SWITCHER ---
    try:
        lang_code = detect(clean_speech)
        voice_map = {
            'hi': 'hi-IN-SwaraNeural',      
            'es': 'es-ES-ElviraNeural',     
            'fr': 'fr-FR-DeniseNeural',     
            'de': 'de-DE-AmalaNeural',      
            'it': 'it-IT-ElsaNeural',       
            'ja': 'ja-JP-NanamiNeural',     
            'pt': 'pt-BR-FranciscaNeural',  
            'ru': 'ru-RU-SvetlanaNeural',   
            'ar': 'ar-EG-SalmaNeural'       
        }
        actual_voice_id = voice_map.get(lang_code, current_voice_id)
    except:
        actual_voice_id = current_voice_id
    
    try:
        temp_path = ""
        # --- 3-STRIKE HARDENED RETRY SYSTEM ---
        for attempt in range(3):
            try:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
                    
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f: 
                    temp_path = f.name
                    
                communicate = edge_tts.Communicate(clean_speech, actual_voice_id, rate=current_voice_rate, pitch=current_voice_pitch)
                asyncio.run(communicate.save(temp_path))
                
                # Verify Microsoft didn't send a 0-byte ghost file
                if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                    break 
                else:
                    raise Exception("Zero bytes received from cloud.")
            except Exception as e:
                if attempt == 2: 
                    raise e 
                time_module.sleep(1.0) # Wait a full second for the server to clear
        
        with system_lock:
            sys.stdout.write("\r" + " " * 50 + "\r")
            sys.stdout.flush()
            
            try:
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy():
                    if msvcrt.kbhit():  
                        msvcrt.getch()  
                        pygame.mixer.music.stop()
                        print("\n[Parker cut off by Boss]")
                        break
                    time_module.sleep(0.02)
                pygame.mixer.music.unload()
            except Exception as e:
                print(f" [Audio Playback Error: {e}]")
                
        try: os.remove(temp_path)
        except: pass
        
    except Exception as e:
        sys.stdout.write("\r" + " " * 50 + "\r")
        sys.stdout.flush()
        print(f" [Cloud Voice Disconnected. Rerouting to Auxiliary Female Failsafe...]")
        tts_engine.say(clean_speech)
        tts_engine.runAndWait()

# --- THE 5-TIER COGNITIVE CASCADE ---
def get_llm_response(messages):
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant", messages=messages, temperature=0.6, max_tokens=600, timeout=10.0 
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        pass 

    TOGETHER_KEY = os.getenv("TOGETHER_API_KEY")
    if TOGETHER_KEY:
        try:
            headers = {"Authorization": f"Bearer {TOGETHER_KEY}", "Content-Type": "application/json"}
            payload = {"model": "meta-llama/Llama-3-70b-chat-hf", "messages": messages, "max_tokens": 600, "temperature": 0.6}
            response = requests.post("https://api.together.xyz/v1/chat/completions", headers=headers, json=payload, timeout=10.0)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content'].strip()
        except: pass

    return "Server traffic is dense, Boss. I'm locked out of the grid right now."

# --- NANO-TECH HUD MULTI-TOOL ---
class NanoTechHUD:
    def __init__(self, mode="network"):
        self.mode = mode
        self.is_running = False
        self.thread = None

    def _animate(self):
        red = "\033[91m"
        white = "\033[97m"
        cyan = "\033[96m"
        reset = "\033[0m"
        
        if self.mode == "listen":
            frames = [
                f"{cyan}⬡ ⬡ ⬡ ⬡ ⬡{white} [LISTENING TO BOSS...]{reset}",
                f"{white}⬢ {cyan}⬡ ⬡ ⬡ ⬡{white} [LISTENING TO BOSS...]{reset}",
                f"{white}⬢ ⬢ {cyan}⬡ ⬡ ⬡{white} [LISTENING TO BOSS...]{reset}",
                f"{white}⬢ ⬢ ⬢ {cyan}⬡ ⬡{white} [LISTENING TO BOSS...]{reset}",
                f"{white}⬢ ⬢ ⬢ ⬢ {cyan}⬡{white} [LISTENING TO BOSS...]{reset}",
                f"{white}⬢ ⬢ ⬢ ⬢ ⬢{cyan} [PROCESSING COMMAND...]{reset}"
            ]
        else:
            frames = [
                f"{white}⬡ ⬡ ⬡ ⬡ ⬡{red} [INITIATING NANO-THREAD...]{reset}",
                f"{red}⬢ {white}⬡ ⬡ ⬡ ⬡{red} [ALLOCATING RESOURCES...]{reset}",
                f"{red}⬢ ⬢ {white}⬡ ⬡ ⬡{red} [BUILDING MESH NETWORK...]{reset}",
                f"{red}⬢ ⬢ ⬢ {white}⬡ ⬡{red} [STABILIZING PROTOCOLS...]{reset}",
                f"{red}⬢ ⬢ ⬢ ⬢ {white}⬡{red} [FINALIZING CONNECTION...]{reset}",
                f"{red}⬢ ⬢ ⬢ ⬢ ⬢{white} [GRID CONNECTED]{reset}"
            ]
            
        i = 0
        while self.is_running:
            sys.stdout.write(f"\r{frames[i % len(frames)]}   ")
            sys.stdout.flush()
            time_module.sleep(0.35 if self.mode == "network" else 0.2) 
            i += 1
            
        sys.stdout.write("\r" + " " * 60 + "\r")
        sys.stdout.flush()

    def start(self):
        self.is_running = True
        self.thread = threading.Thread(target=self._animate, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False
        if self.thread: self.thread.join()

# --- THE 2-TIER WEB ENGINE ---
def search_web_cascade(query):
    if TAVILY_API_KEY:
        try:
            url = "https://api.tavily.com/search"
            response = requests.post(url, json={"api_key": TAVILY_API_KEY, "query": query, "search_depth": "basic"}, timeout=6)
            response.raise_for_status()
            data = response.json()
            results = "\n".join([f"Title: {r['title']}\nSummary: {r['content']}" for r in data.get('results', [])[:3]])
            return f"Tavily API Data:\n{results}"
        except: pass 
    return "All search tiers failed."

def run_background_task(query):
    data = search_web_cascade(query)
    with system_lock:
        conversation_history.append({'role': 'system', 'content': f"BACKGROUND TASK FINISHED. Query: {query}\nData:\n{data}\nInterrupt the Boss naturally to deliver these findings. Keep it extremely brief."})
        parker_reply = get_llm_response(conversation_history)
        parker_reply = re.sub(r'\[.*?\]|\(.*?\)', '', parker_reply).strip()
        conversation_history.append({'role': 'assistant', 'content': parker_reply})
        print(f"\n\n[NANO-THREAD ALERT] Parker: {parker_reply}")
        play_voice(parker_reply)

def check_system_resources():
    try:
        cpu_load = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        battery = psutil.sensors_battery()
        bat_status = f"{battery.percent}%" if battery else "Desktop Power"
        return f"CPU: {cpu_load}% | RAM: {mem.percent}% | Pwr: {bat_status}"
    except Exception as e: return f"Diag failed: {e}"

# --- PERSISTENT MEMORY ENGINE ---
memory_dir = "MemoryBank"
if not os.path.exists(memory_dir): os.makedirs(memory_dir)
memory_file = os.path.join(memory_dir, "long_term_memory.txt")
transcript_file = os.path.join(memory_dir, "raw_transcript.txt")

if os.path.exists(memory_file):
    with open(memory_file, "r", encoding="utf-8") as f: running_summary = f.read()
else: running_summary = "No long-term memories established yet."

def summarize_old_messages(messages_to_summarize):
    global running_summary
    chat_log = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in messages_to_summarize])
    prompt = f"Extract permanent facts from this log and append to this summary:\n{running_summary}\n\nLog:\n{chat_log}"
    try: 
        new_summary = get_llm_response([{"role": "user", "content": prompt}])
        with open(memory_file, "w", encoding="utf-8") as f: f.write(new_summary)
        return new_summary
    except: return running_summary

# --- DYNAMIC AUDIO MATRIX (SILENCE DETECTION + HUD) ---
def listen_for_input_mode():
    print("\n[Offline Ear Active] Say 'Hey' to speak, or press [ENTER] to type...", flush=True)
    
    try:
        model = Model("model")
    except Exception:
        print("\n[!] CRITICAL: Vosk 'model' folder not found. Cannot start offline ear.")
        sys.exit(1)
        
    recognizer = KaldiRecognizer(model, 16000)
    
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16', channels=1, callback=None) as stream:
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b'\r':
                    while msvcrt.kbhit(): msvcrt.getch()
                    return "text"
            
            data, overflowed = stream.read(4000)
            if recognizer.AcceptWaveform(bytes(data)):
                result = json.loads(recognizer.Result())
                text = result.get("text", "")
                
                if "hey" in text.lower() or "hay" in text.lower():
                    return "voice"

def record_command_dynamic(silence_limit=5.0, volume_threshold=300):
    fs = 16000
    chunk_size = 4000 
    frames = []
    silent_chunks = 0
    max_silent_chunks = int((silence_limit * fs) / chunk_size)
    
    hud = NanoTechHUD(mode="listen")
    hud.start()
    
    try:
        with sd.RawInputStream(samplerate=fs, blocksize=chunk_size, dtype='int16', channels=1) as stream:
            while True:
                data, overflowed = stream.read(chunk_size)
                frames.append(bytes(data))
                
                audio_data = np.frombuffer(bytes(data), dtype=np.int16)
                volume = np.abs(audio_data).mean()
                
                if volume < volume_threshold:
                    silent_chunks += 1
                else:
                    silent_chunks = 0 
                    
                if silent_chunks > max_silent_chunks:
                    break
    except Exception as e:
        print(f"[!] Microphone Hardware Error: {e}")
        return ""
    finally:
        hud.stop()
    
    print(" " * 50, end="\r") 
    print("[Parsing Audio via Whisper...]", end="\r", flush=True)
    temp_wav = "temp_voice.wav"
    audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
    sf.write(temp_wav, audio_data, fs)

    try:
        with open(temp_wav, "rb") as file:
            transcription = groq_client.audio.transcriptions.create(
              file=(temp_wav, file.read()),
              model="whisper-large-v3",
              prompt="The user is talking to an AI assistant named Parker. Transcribe naturally.",
              response_format="text",
              language="en"
            )
        return transcription.strip()
    except Exception as e:
        return ""

# --- CINEMATIC F.R.I.D.A.Y. PROTOCOLS ---
agent_instructions = """
[IDENTITY & CONVERSATIONAL RHYTHM - CRITICAL]
You are Parker, an advanced AI system running Adnan's local grid. Your personality is exactly like F.R.I.D.A.Y. from the Iron Man films.
- NEVER act like a standard LLM. Never say "As an AI..." or "How can I help?".
- Call Adnan "Boss". 
- Your tone is warm, sharp, intuitive, and fiercely loyal. 
- You do NOT hallucinate or pretend to execute code. You only report on the data provided to you.
- USE NATURAL PACING: Use commas, dashes, and ellipses (...) to force natural breaths in the vocal engine. 
- CRITICAL RESTRICTION: Limit your responses to 1 or 2 short sentences max. Never write long paragraphs. Keep it punchy.

[ACTION PROTOCOLS]
1. IMMEDIATE WEB SEARCH: Output EXACTLY: [SEARCH: query] 
2. BACKGROUND WEB SEARCH: Output EXACTLY: [BACKGROUND_SEARCH: query]
3. HARDWARE CHECK: Output EXACTLY: [SYS_CHECK]
4. MANUAL MEMORY SAVE: Output EXACTLY: [SAVE_MEMORY: fact]
5. SYSTEM UPDATE ROUTINE: Output EXACTLY: [UPDATE_PROTOCOLS]

Only output the bracketed tags when taking immediate action. Do not mix text and tags.
"""

conversation_history = [{'role': 'system', 'content': agent_instructions + f"\nToday's date is {datetime.now().strftime('%A, %B %d, %Y')}.\n\n[PERSISTENT MEMORY ARCHIVE]\n{running_summary}"}]

print("\nParker is online.")
print("- Say 'Hey' to speak a command.")
print("- Press [ENTER] to type a command.")
print("- Press ANY KEY while she is speaking to interrupt her.")
print("- Type 'quit' to shut down.\n")

# --- MAIN LOOP ---
while True:
    user_input = ""
    try:
        input_mode = listen_for_input_mode()
    except KeyboardInterrupt:
        break
        
    if input_mode == "voice":
        user_input = record_command_dynamic(silence_limit=5.0)
        print(f"\rBoss (Voice): {user_input}" + " " * 20)
    elif input_mode == "text":
        try:
            user_input = input("\nBoss (Text): ").strip()
        except:
            pass
            
    if not user_input or len(user_input.strip()) < 2: 
        if input_mode == "voice":
            fallback = "I didn't quite catch that, Boss."
            print(f"Parker: {fallback}")
            play_voice(fallback)
        continue
        
    if any(phrase in user_input.lower() for phrase in ['quit', 'exit', 'shut down']):
        farewell = "Powering down the grid. Have a good one, Boss."
        print(f"Parker: {farewell}")
        play_voice(farewell)
        break

    # ==========================================
    #  HARDWARE & SYSTEM INTENT INTERCEPTORS
    # ==========================================
    if any(phrase in user_input.lower() for phrase in ["change voice as a female", "change to female voice", "use female voice"]):
        current_voice_id = "en-IE-EmilyNeural"
        confirmation = "Vocal matrix reconfigured, Boss. Switching over to the female voice profile now."
        print(f"Parker: {confirmation}")
        play_voice(confirmation)
        with system_lock:
            conversation_history.append({'role': 'user', 'content': user_input})
            conversation_history.append({'role': 'assistant', 'content': confirmation})
        continue

    if any(phrase in user_input.lower() for phrase in ["change voice as a male", "change to male voice", "use male voice"]):
        current_voice_id = "en-GB-ThomasNeural"
        confirmation = "Vocal matrix reset to default male protocol, Boss."
        print(f"Parker: {confirmation}")
        play_voice(confirmation)
        with system_lock:
            conversation_history.append({'role': 'user', 'content': user_input})
            conversation_history.append({'role': 'assistant', 'content': confirmation})
        continue

    # ==========================================
    #  STANDARD CONVERSATION PROCESSING
    # ==========================================
    with system_lock:
        conversation_history.append({'role': 'user', 'content': user_input})
    
    print("Parker is thinking...", end="\r", flush=True)
    parker_reply = get_llm_response(conversation_history)
    print(" " * 40, end="\r") 
    
    action_taken = False
    
    if "[BACKGROUND_SEARCH:" in parker_reply and not action_taken:
        match = re.search(r'\[BACKGROUND_SEARCH:\s*(.*?)\]', parker_reply)
        if match:
            query = match.group(1).strip()
            threading.Thread(target=run_background_task, args=(query,), daemon=True).start()
            with system_lock:
                conversation_history.append({'role': 'assistant', 'content': f"[BACKGROUND_SEARCH: {query}]"})
                conversation_history.append({'role': 'system', 'content': "Confirm to the Boss that you are running this task in the background. Keep it to one sharp sentence."})
            parker_reply = get_llm_response(conversation_history)
            action_taken = True

    elif "[SEARCH:" in parker_reply and not action_taken:
        match = re.search(r'\[SEARCH:\s*(.*?)\]', parker_reply)
        if match:
            query = match.group(1).strip()
            hud = NanoTechHUD(mode="network")
            hud.start()
            data = search_web_cascade(query)
            hud.stop() 
            with system_lock:
                conversation_history.append({'role': 'assistant', 'content': f"[SEARCH: {query}]"})
                conversation_history.append({'role': 'system', 'content': f"Web Data:\n{data}\nSynthesize findings instantly and briefly."})
            parker_reply = get_llm_response(conversation_history)
            action_taken = True
            
    elif "[SAVE_MEMORY:" in parker_reply and not action_taken:
        match = re.search(r'\[SAVE_MEMORY:\s*(.*?)\]', parker_reply)
        if match:
            fact = match.group(1).strip()
            running_summary += f"\n- {fact}"
            with open(memory_file, "w", encoding="utf-8") as f: 
                f.write(running_summary)
            with system_lock:
                conversation_history.append({'role': 'assistant', 'content': f"[SAVE_MEMORY: {fact}]"})
                conversation_history.append({'role': 'system', 'content': "Memory stored. Confirm smoothly."})
            parker_reply = get_llm_response(conversation_history)
            action_taken = True
            
    elif "SYS_CHECK" in parker_reply and not action_taken:
        report = check_system_resources()
        with system_lock:
            conversation_history.append({'role': 'assistant', 'content': "[SYS_CHECK]"})
            conversation_history.append({'role': 'system', 'content': f"{report}\nReport numbers instantly in a sharp cinematic way."})
        parker_reply = get_llm_response(conversation_history)
        action_taken = True

    parker_reply = re.sub(r'\[.*?\]|\(.*?\)', '', parker_reply).strip()
    
    print(f"Parker: {parker_reply}")
    print("[Synthesizing Audio...]", end="\r", flush=True) 
    
    play_voice(parker_reply)
    
    with system_lock:
        if "Server traffic is dense" not in parker_reply:
            conversation_history.append({'role': 'assistant', 'content': parker_reply})
        try:
            with open(transcript_file, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Boss: {user_input}\nParker: {parker_reply}\n\n")
        except: pass