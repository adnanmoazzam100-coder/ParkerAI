"""
piper_tts.py — Local, offline, free-forever text-to-speech for Parker using Piper.

Replaces ElevenLabs entirely. No API key, no internet, no quota, no expiry.
Requires two files sitting next to core.py:
    en_GB-semaine-medium.onnx
    en_GB-semaine-medium.onnx.json
(Download both from https://huggingface.co/rhasspy/piper-voices)

Usage from core.py:
    import piper_tts
    audio_bytes = piper_tts.synthesize_to_wav_bytes("Hello, Boss.")
    # audio_bytes is a complete in-memory WAV file, ready for pygame.mixer
"""

import os
import io
import wave

TTS_ENABLED = False
_init_error = None
_voice = None

VOICE_MODEL_NAME = "en_GB-semaine-medium"  # change this if you swap voices later

try:
    from piper import PiperVoice

    _model_path = os.path.join(os.path.dirname(__file__), f"{VOICE_MODEL_NAME}.onnx")
    _config_path = os.path.join(os.path.dirname(__file__), f"{VOICE_MODEL_NAME}.onnx.json")

    if not os.path.isfile(_model_path):
        raise FileNotFoundError(
            f"Piper voice model not found at '{_model_path}'. "
            f"Download '{VOICE_MODEL_NAME}.onnx' and '{VOICE_MODEL_NAME}.onnx.json' "
            f"from https://huggingface.co/rhasspy/piper-voices and place them next to core.py."
        )
    if not os.path.isfile(_config_path):
        raise FileNotFoundError(
            f"Piper voice config not found at '{_config_path}'. "
            f"Make sure '{VOICE_MODEL_NAME}.onnx.json' is in the same folder as core.py."
        )

    _voice = PiperVoice.load(_model_path, config_path=_config_path)
    TTS_ENABLED = True

except Exception as e:
    _init_error = str(e)


def synthesize_to_wav_bytes(text):
    """
    Converts text to speech using Piper and returns a complete WAV file as bytes,
    ready to be written to a temp file and played with pygame.mixer.
    Returns None if Piper failed to initialise or synthesis fails for any reason.
    """
    if not TTS_ENABLED or not text:
        return None

    try:
        wav_buffer = io.BytesIO()
        wav_file = None

        for chunk in _voice.synthesize(text):
            if wav_file is None:
                wav_file = wave.open(wav_buffer, "wb")
                wav_file.setnchannels(chunk.sample_channels)
                wav_file.setsampwidth(chunk.sample_width)
                wav_file.setframerate(chunk.sample_rate)
            wav_file.writeframes(chunk.audio_int16_bytes)

        if wav_file is not None:
            wav_file.close()
            return wav_buffer.getvalue()
        return None

    except Exception as e:
        print(f"\n[Piper TTS Error: {e}]")
        return None