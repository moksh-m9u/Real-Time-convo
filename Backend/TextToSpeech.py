import pygame
import asyncio
import edge_tts
import os
from dotenv import dotenv_values

env_vars = dotenv_values(".env")
assistant_voice = env_vars.get("Assistantvoice")

async def text_to_audio_file(text):
    file_path = r"Data\speech.mp3"
    if os.path.exists(file_path):
        os.remove(file_path)
    communicate = edge_tts.Communicate(text, assistant_voice, pitch='+5Hz', rate='+13%')
    await communicate.save(file_path)

async def TTS(text, stop_func=lambda r=None: True):
    try:
        await text_to_audio_file(text)
        pygame.mixer.init()
        pygame.mixer.music.load(r"Data\speech.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            if not stop_func():
                break
            await asyncio.sleep(0.01)
        return True
    except Exception as e:
        print(f"Error in TTS: {e}")
        return False
    finally:
        try:
            stop_func(False)
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except Exception as e:
            print(f"Error in Finally Block: {e}")

if __name__ == "__main__":
    async def test_tts():
        text = input("Enter the text: ")
        await TTS(text)
    asyncio.run(test_tts())
