import pygame
import os
import time

pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
pygame.mixer.init()
pygame.mixer.set_num_channels(8) 

def play_squid_music():
    try:
        if not os.path.exists("squid.mp3"):
            print("Error: squid.mp3 file not found!")
            return False
        
        pygame.mixer.music.load("squid.mp3")
        pygame.mixer.music.play(-1) 
        pygame.mixer.music.set_volume(0.6)  
        
        print("Playing squid.mp3 (looping continuously)")
        return True
        
    except pygame.error as e:
        print(f"Error playing music: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def play_green_light():
    try:
        if not os.path.exists("green-light.mp3"):
            print("Error: green-light.mp3 file not found!")
            return False
        
        green_sound = pygame.mixer.Sound("green-light.mp3")
        green_sound.set_volume(1.0)
        green_sound.play()
        
        print("Playing green-light.mp3 (overlay on squid music)")
        return True
        
    except pygame.error as e:
        print(f"Error playing green-light sound: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def play_red_light():
    try:
        if not os.path.exists("red-light.mp3"):
            print("Error: red-light.mp3 file not found!")
            return False
        
        red_sound = pygame.mixer.Sound("red-light.mp3")
        red_sound.set_volume(1.0)  
        red_sound.play()
        
        print("Playing red-light.mp3 (overlay on squid music)")
        return True
        
    except pygame.error as e:
        print(f"Error playing red-light sound: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def play_cycle_music(elapsed_time, cycle_duration=6):
    """
    Play green-light.mp3 or red-light.mp3 based on 6-second cycles
    Returns True if music was changed, False otherwise
    """
    cycle_position = elapsed_time % (cycle_duration * 2) 
    motion_detection_active = cycle_position >= cycle_duration
    
    if motion_detection_active:
         return play_red_light() 
    else:    
        return play_green_light()

def get_current_cycle_state(elapsed_time, cycle_duration=6):
    adjusted_time = elapsed_time - 5.8
    
    if adjusted_time < 0:
        return 'red', 5.8 - elapsed_time
    
    cycle_position = adjusted_time % (cycle_duration * 2)
    motion_detection_active = cycle_position >= cycle_duration
    
    if motion_detection_active:
        remaining = (cycle_duration * 2) - cycle_position
        return 'red', remaining
    else:
        remaining = cycle_duration - cycle_position
        return 'green', remaining

def stop_music():
    try:
        pygame.mixer.music.stop()
        pygame.mixer.stop() 
        print("All music and sounds stopped")
    except:
        print("No music to stop")

def is_music_playing():
    try:
        return pygame.mixer.music.get_busy()
    except:
        return False

def set_volume(volume):
    """Set squid music volume (0.0 to 1.0)"""
    try:
        pygame.mixer.music.set_volume(volume)
        print(f"Squid volume set to {volume}")
    except:
        print("Error setting volume")

class CycleMusic:
    """Class to manage cycling between green-light and red-light sound effects while squid music plays"""
    
    def __init__(self, cycle_duration=6):
        self.cycle_duration = cycle_duration
        self.last_state = None
        self.start_time = None
        
        try:
            if os.path.exists("green-light.mp3"):
                self.green_sound = pygame.mixer.Sound("green-light.mp3")
                self.green_sound.set_volume(1.0)
            else:
                self.green_sound = None
                print("Warning: green-light.mp3 not found")
                
            if os.path.exists("red-light.mp3"):
                self.red_sound = pygame.mixer.Sound("red-light.mp3")
                self.red_sound.set_volume(1.0)
            else:
                self.red_sound = None
                print("Warning: red-light.mp3 not found")
                
        except Exception as e:
            print(f"Warning: Could not pre-load sound effects: {e}")
            self.green_sound = None
            self.red_sound = None
    
    def start(self):
        """Start the sound effect cycle (squid music should already be playing)"""
        self.start_time = time.time()
        self.last_state = None
        print("Started cycling green/red light sounds (squid music continues)")
    
    def update(self):
        """Update sound effects based on current time (squid music continues playing)"""
        if self.start_time is None:
            return "unknown", 0
        
        elapsed_time = time.time() - self.start_time
        current_state, remaining = get_current_cycle_state(elapsed_time, self.cycle_duration)

        if current_state != self.last_state:
            if current_state == 'green' and self.green_sound:
                self.green_sound.play()
                print("Playing green-light sound (over squid music)")
            elif current_state == 'red' and self.red_sound:
                self.red_sound.play()
                print("Playing red-light sound (over squid music)")
            
            self.last_state = current_state
        
        return current_state, remaining

if __name__ == "__main__":
    print("Testing cycle music (green-light/red-light every 6 seconds)")
    print("Press Ctrl+C to stop")
    
    play_squid_music()
    
    cycle_music = CycleMusic(cycle_duration=6)
    cycle_music.start()
    
    try:
        while True:
            state, remaining = cycle_music.update()
            print(f"Squid music + {state}-light, Time left: {remaining:.1f}s", end='\r')
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nStopping music...")
        stop_music()