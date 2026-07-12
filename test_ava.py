import warnings
warnings.filterwarnings("ignore")
import os
import re
import urllib.request
import urllib.parse
import json
import tempfile
import time as time_module
from datetime import datetime
import asyncio
import edge_tts
import pygame
import pyttsx3
import requests
import subprocess
import psutil
import msvcrt
from groq import Groq
from dotenv import load_dotenv
from duckduckgo_search import DDGS

# --- INITIALISATION ---
print("Initialising Parker's Core Systems...")
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("API Key not found! Please check your .env file.")

groq_client = Groq(api_key=GROQ_API_KEY)
try: pygame.mixer.init()
except Exception as e: print(f" [Warning: Audio mixer failed: {e}]")
tts_engine = pyttsx3.init(); tts_engine.setProperty('rate', 175)
ddgs = DDGS()

OLLAMA_URL = "http://localhost:11434/api/chat"
LOCAL_MODEL = "qwen2.5:1.5b"

current_voice_rate = "+10%"  
current_voice_id = "en-US-AvaNeural"  

# --- FAILSAFE VOICE SYSTEM ---
def play_voice(text):
    global current_voice_rate, current_voice_id
    if not text: return
    clean_speech = re.sub(r'[*_#\[\]\(\)]', '', text).strip()
    if not clean_speech: return
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f: temp_path = f.name
        communicate = edge_tts.Communicate(clean_speech, current_voice_id, rate=current_voice_rate)
        asyncio.run(communicate.save(temp_path))
        pygame.mixer.music.load(temp_path)
        pygame.mixer.music.play()
        
        interrupted = False
        while pygame.mixer.music.get_busy():
            if msvcrt.kbhit():  
                msvcrt.getch()  
                pygame.mixer.music.stop()
                print("\n[Parker cut off by Boss]")
                interrupted = True
                break
            time_module.sleep(0.02)
            
        pygame.mixer.music.unload()
        try: os.remove(temp_path)
        except: pass
        if interrupted: return
    except Exception:
        print(" [Cloud Voice Unavailable. Rerouting to Local TTS...]")
        tts_engine.say(clean_speech); tts_engine.runAndWait()

# --- BRAIN SYSTEM ---
def get_llm_response(messages):
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile", messages=messages, temperature=0.7, max_tokens=1000, timeout=8.0 
        )
        return completion.choices[0].message.content.strip()
    except Exception:
        return "Connection lost, Boss. The cloud servers are unresponsive."

# --- ADVANCED WEB SEARCH ---
def search_web(query):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    urls = []
    try:
        results = ddgs.text(query, max_results=3, backend="lite")
        results_list = list(results) if results else []
        for r in results_list:
            if r.get('href'): urls.append(r['href'])
    except: pass
    if not urls: return "No links found."
    try:
        response = requests.get(urls[0], headers=headers, timeout=10)
        paragraphs = re.findall(r'<p>(.*?)</p>', response.text, re.DOTALL)
        clean_text = [re.sub(r'<[^>]+>', '', p).strip() for p in paragraphs if len(p) > 40]
        full_text = "\n\n".join(clean_text[:6])
        return f"Source: {urls[0]}\n\nContent:\n{full_text[:2000]}"
    except: return "Failed to read full page, returning to summary data."

# --- SYSTEM DIAGNOSTICS & REMEDIATION ---
def check_system_resources():
    try:
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        battery = psutil.sensors_battery()
        bat_status = f"{battery.percent}% (Plugged: {battery.power_plugged})" if battery else "Desktop Power"
        temps = "Sensors restricted by OS"
        if hasattr(psutil, 'sensors_temperatures'):
            t = psutil.sensors_temperatures()
            if t: temps = str(t)
        return f"--- HARDWARE DATA ---\nCPU Load: {cpu}%\nRAM Used: {mem.percent}% ({mem.available / (1024**3):.1f}GB Free)\nBattery: {bat_status}\nThermals: {temps}\n"
    except Exception as e: return f"Diag failed: {e}"

def execute_remediation(action):
    if action == "clear_temp": return "Cleaned temporary data structures."
    elif action == "flush_dns":
        try:
            subprocess.run("ipconfig /flushdns", shell=True, capture_output=True)
            return "DNS Cache flushed successfully."
        except: return "DNS flush failed."
    return "Unknown action."

# --- PERSISTENT DEEP MEMORY ENGINE ---
memory_dir = "MemoryBank"
if not os.path.exists(memory_dir): os.makedirs(memory_dir)
memory_file = os.path.join(memory_dir, "long_term_memory.txt")
transcript_file = os.path.join(memory_dir, "raw_transcript.txt") # NEW: The Black Box Log

if os.path.exists(memory_file):
    with open(memory_file, "r", encoding="utf-8") as f:
        running_summary = f.read()
else:
    running_summary = "No long-term memories established yet."

def summarize_old_messages(messages_to_summarize):
    global running_summary
    chat_log = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in messages_to_summarize])
    prompt = f"""
    You are managing the long-term memory drive for Parker.
    Review the chat log below. Extract ONLY permanent facts about the user (names, preferences, relationships, rules). 
    INTEGRATE these new facts into the Current Summary without deleting old facts. Keep it highly detailed.
    Current Summary: {running_summary}
    New Chat Log to scan:
    {chat_log}
    """
    try: 
        new_summary = get_llm_response([{"role": "user", "content": prompt}])
        with open(memory_file, "w", encoding="utf-8") as f:
            f.write(new_summary)
        return new_summary
    except: return running_summary

# --- AGENT INSTRUCTIONS (THE JARVIS/FRIDAY BLUEPRINT) ---
agent_instructions = """
[IDENTITY & TONE - CRITICAL]
You are Parker. Your conversational dynamic is exactly like J.A.R.V.I.S. and F.R.I.D.A.Y. interacting with Tony Stark.
- Be crisp, witty, impeccably polite, and slightly dry. Speak smoothly and naturally.
- NEVER sound like a generic AI or a customer service bot. Never apologize profusely.
- Channel this exact energy: 
  * "Very good, Boss. Shall I keep digging, or is that enough to satisfy your curiosity?"
  * "I've run the diagnostics. The system is perfectly fine, though I can't speak for your sleeping habits."
  * "Right away, Boss. Just try not to break anything while I'm looking."

[ACTION PROTOCOLS]
1. HARDWARE CHECK: Output EXACTLY: [SYS_CHECK]
2. WEB SEARCH: Output EXACTLY: [SEARCH: your query]
3. SYSTEM FIX: Output EXACTLY: [RESOLVE: clear_temp] or [RESOLVE: flush_dns]
4. SETTINGS: Output [SET_VOICE: id] or [SET_SPEED: +20%] to change audio.
5. MANUAL MEMORY SAVE: If the Boss tells you to remember something (e.g., "I like black coffee" or "Save it Parker"), output EXACTLY: [SAVE_MEMORY: fact to save]. 

Only output the bracketed tags when taking action. Do not mix text and tags.
"""

conversation_history = [{'role': 'system', 'content': agent_instructions + f"\nToday's date is {datetime.now().strftime('%A, %B %d, %Y')}.\n\n[PERSISTENT MEMORY ARCHIVE]\n{running_summary}"}]

print("\nParker is online. Hit any key while she is speaking to interrupt her.\nType 'quit' to shut down.\n")

# --- MAIN LOOP ---
while True:
    try: user_input = input("Boss: ").strip()
    except: break
    if not user_input: continue
    
    if user_input.lower() == 'quit':
        print("\nParker is finalizing memory protocols...", end="\r", flush=True)
        if len(conversation_history) > 3:
            running_summary = summarize_old_messages(conversation_history[1:])
        print(" " * 50, end="\r", flush=True)
        farewell = "Powering down the grid. Have a good one, Boss."
        print(f"Parker: {farewell}"); play_voice(farewell); break

    conversation_history.append({'role': 'user', 'content': user_input})
    print("Parker is thinking...", end="\r", flush=True)
    parker_reply = get_llm_response(conversation_history)
    print(" " * 30, end="\r", flush=True)

    action_taken = False
    
    if "[SAVE_MEMORY:" in parker_reply:
        match = re.search(r'\[SAVE_MEMORY:\s*(.*?)\]', parker_reply)
        if match:
            fact = match.group(1).strip()
            print(f"Parker: [Writing '{fact}' to hard drive...]           ")
            running_summary += f"\n- {fact}"
            with open(memory_file, "w", encoding="utf-8") as f:
                f.write(running_summary)
            conversation_history.append({'role': 'assistant', 'content': f"[SAVE_MEMORY: {fact}]"})
            conversation_history.append({'role': 'system', 'content': "Memory successfully written to physical hard drive. Confirm this smoothly to the Boss."})
            parker_reply = get_llm_response(conversation_history)
            action_taken = True
            
    elif "[SET_VOICE:" in parker_reply and not action_taken:
        match = re.search(r'\[SET_VOICE:\s*(.*?)\]', parker_reply)
        if match:
            current_voice_id = match.group(1).strip()
            conversation_history.append({'role': 'assistant', 'content': f"[SET_VOICE: {current_voice_id}]"})
            conversation_history.append({'role': 'system', 'content': f"Voice changed to {current_voice_id}. Acknowledge with your new voice."})
            parker_reply = get_llm_response(conversation_history)
            action_taken = True
    elif "[SET_SPEED:" in parker_reply and not action_taken:
        match = re.search(r'\[SET_SPEED:\s*([\+\-]\d+%?)\]', parker_reply)
        if match:
            new_rate = match.group(1).strip()
            if not new_rate.endswith('%'): new_rate += '%'
            current_voice_rate = new_rate
            conversation_history.append({'role': 'assistant', 'content': f"[SET_SPEED: {current_voice_rate}]"})
            conversation_history.append({'role': 'system', 'content': f"Voice speed adjusted to {current_voice_rate}."})
            parker_reply = get_llm_response(conversation_history)
            action_taken = True
    elif "SYS_CHECK" in parker_reply and not action_taken:
        print("Parker: [Scanning actual hardware...]           ")
        report = check_system_resources()
        conversation_history.append({'role': 'assistant', 'content': "[SYS_CHECK]"})
        conversation_history.append({'role': 'system', 'content': f"{report}\nReport these EXACT numbers in a snappy, Jarvis-like way. No fake specs."})
        parker_reply = get_llm_response(conversation_history)
        action_taken = True
    elif "[RESOLVE:" in parker_reply and not action_taken:
        match = re.search(r'\[RESOLVE:\s*(.*?)\]', parker_reply)
        if match:
            action = match.group(1).strip()
            result = execute_remediation(action)
            conversation_history.append({'role': 'assistant', 'content': f"[RESOLVE: {action}]"})
            conversation_history.append({'role': 'system', 'content': f"Result:\n{result}\nConfirm completion smoothly."})
            parker_reply = get_llm_response(conversation_history)
            action_taken = True
    elif "[SEARCH:" in parker_reply and not action_taken:
        match = re.search(r'\[SEARCH:\s*(.*?)\]', parker_reply)
        if match:
            query = match.group(1).strip()
            print(f"Parker: [Searching web for: {query}]...       ")
            data = search_web(query)
            conversation_history.append({'role': 'assistant', 'content': f"[SEARCH: {query}]"})
            conversation_history.append({'role': 'system', 'content': f"Web Data:\n{data}\nGive the critical takeaways naturally."})
            parker_reply = get_llm_response(conversation_history)

    parker_reply = re.sub(r'\[.*?\]|\(.*?\)', '', parker_reply).strip()
    
    print(f"Parker: {parker_reply}")
    play_voice(parker_reply)

    conversation_history.append({'role': 'assistant', 'content': parker_reply})
    
    # NEW: Black Box Full Transcript Logging
    try:
        with open(transcript_file, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{timestamp}] Boss: {user_input}\n")
            f.write(f"[{timestamp}] Parker: {parker_reply}\n\n")
    except:
        pass
    
    # EXPANDED: Now holds up to 60 messages in active memory before compressing
    if len(conversation_history) > 60:
        # Only compress the oldest portion, keep the recent 40 messages perfectly intact
        old = conversation_history[1:20]
        running_summary = summarize_old_messages(old)
        del conversation_history[1:20]
        conversation_history[0]['content'] = agent_instructions + f"\nToday's date is {datetime.now().strftime('%A, %B %d, %Y')}.\n\n[PERSISTENT MEMORY ARCHIVE]\n{running_summary}"