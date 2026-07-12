from elevenlabs import ElevenLabs

client = ElevenLabs(api_key="sk_143304dedb04bf7a058042b4a230f0441635b6d20b3d2802")

audio = client.text_to_speech.convert(
    text="test",
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    model_id="eleven_multilingual_v2"
)

audio_bytes = b"".join(audio)
print(f"Got {len(audio_bytes)} bytes of audio")

with open("test.mp3", "wb") as f:
    f.write(audio_bytes)

print("Saved test.mp3 — now open it manually and check if it plays.")