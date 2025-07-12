import pygame
import os

def play_squid_music():
    try:
        pygame.mixer.init()
        
        if not os.path.exists("squid.mp3"):
            print("Error: squid.mp3 file not found!")
            return False
        pygame.mixer.music.load("squid.mp3")
        pygame.mixer.music.play()
        
        print("Playing squid.mp3")
        return True
        
    except pygame.error as e:
        print(f"Error playing music: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def stop_music():
    try:
        pygame.mixer.music.stop()
        print("Music stopped")
    except:
        print("No music to stop")

def is_music_playing():
    try:
        return pygame.mixer.music.get_busy()
    except:
        return False

def set_volume(volume):
    """Set music volume (0.0 to 1.0)"""
    try:
        pygame.mixer.music.set_volume(volume)
        print(f"Volume set to {volume}")
    except:
        print("Error setting volume")

if __name__ == "__main__":
    play_squid_music()
    try:
        while is_music_playing():
            pygame.time.wait(100)
    except KeyboardInterrupt:
        print("\nStopping music...")
        stop_music()