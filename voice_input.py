"""
voice_input.py — Defensive wrapper for Parker.
Prevents binary segmentation faults on Python 3.14.
"""
VOICE_INPUT_ENABLED = False
_init_error = "Local voice libraries disabled to prevent Python 3.14 interpreter crashes."

def start_listening():
    return False

def stop_listening():
    pass

def pause_listening():
    pass

def resume_listening():
    pass

def was_interrupted():
    return False

def get_voice_text_nonblocking():
    return None