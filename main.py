import keyboard
import pyperclip
import threading
import time
import json
import os
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='switchlang.log'
)
logger = logging.getLogger('SwitchLang')

class SwitchLang:
    def __init__(self):
        self.buffer = ""
        self.is_running = True
        self.word_mappings = {
            # Thai to English mappings
            "l;ylfu8iy[": "สวัสดีครับ",
            "wxwso,k": "ไปไหนมา",
            # More mappings can be added here
        }
        self.thai_to_eng_mappings = self.load_mappings("thai_to_eng.json")
        self.eng_to_thai_mappings = self.load_mappings("eng_to_thai.json")
        self.recent_words = []
        self.tray_icon = None
        self.init_tray_icon()
        
    def load_mappings(self, filename):
        """Load language mappings from JSON file."""
        file_path = Path(os.path.dirname(os.path.abspath(__file__))) / filename
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load mappings from {filename}: {e}")
                return {}
        else:
            logger.info(f"Mapping file {filename} not found, using default mappings")
            # Create a default file with some sample mappings
            if filename == "thai_to_eng.json":
                default_mappings = {
                    "l;ylfu8iy[": "สวัสดีครับ",
                    "wxwso,k": "ไปไหนมา",
                }
            else:
                default_mappings = {}
                
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(default_mappings, f, ensure_ascii=False, indent=4)
            except Exception as e:
                logger.error(f"Failed to create default mapping file {filename}: {e}")
                
            return default_mappings

    def save_mappings(self):
        """Save current mappings to JSON files."""
        try:
            with open('thai_to_eng.json', 'w', encoding='utf-8') as f:
                json.dump(self.thai_to_eng_mappings, f, ensure_ascii=False, indent=4)
            with open('eng_to_thai.json', 'w', encoding='utf-8') as f:
                json.dump(self.eng_to_thai_mappings, f, ensure_ascii=False, indent=4)
            logger.info("Mappings saved successfully")
        except Exception as e:
            logger.error(f"Failed to save mappings: {e}")

    def create_tray_icon(self):
        """Create a simple icon for the system tray."""
        image = Image.new('RGB', (64, 64), color=(0, 150, 200))
        draw = ImageDraw.Draw(image)
        draw.rectangle([(16, 16), (48, 48)], fill=(255, 255, 255))
        draw.text((20, 20), "RL", fill=(0, 100, 150))
        return image

    def init_tray_icon(self):
        """Initialize system tray icon with menu."""
        icon_image = self.create_tray_icon()
        menu = Menu(
            MenuItem('Add New Mapping', self.show_add_mapping_dialog),
            MenuItem('Save Mappings', lambda: self.save_mappings()),
            MenuItem('Exit', self.exit_app)
        )
        self.tray_icon = Icon('SwitchLang', icon_image, 'SwitchLang', menu)

    def show_add_mapping_dialog(self):
        """Show dialog to add new mapping. In a real app, use a proper GUI dialog."""
        # This is a placeholder for a real dialog
        # In a real application, you would use tkinter or another GUI framework
        logger.info("Add mapping dialog requested (placeholder)")
        # For demonstration, add a hardcoded mapping
        self.thai_to_eng_mappings["vbiyd"] = "สบาย"
        self.save_mappings()

    def exit_app(self):
        """Shut down the application."""
        self.is_running = False
        if self.tray_icon:
            self.tray_icon.stop()
        logger.info("Application shutting down")

    def on_key_event(self, event):
        """Handle keyboard events."""
        if not self.is_running:
            return
            
        if event.event_type == keyboard.KEY_DOWN:
            # Handle Space key to check and correct word
            if event.name == 'space':
                if self.buffer:
                    self.check_and_correct_word()
                self.buffer += ' '
            # Handle Enter key
            elif event.name == 'enter':
                self.buffer = ""
            # Handle Backspace
            elif event.name == 'backspace':
                if self.buffer:
                    self.buffer = self.buffer[:-1]
            # Handle other printable keys
            elif len(event.name) == 1 or event.name in ['shift', 'ctrl', 'alt']:
                if event.name not in ['shift', 'ctrl', 'alt']:
                    self.buffer += event.name
            # Handle special character keys
            elif hasattr(event, 'scan_code'):
                char = keyboard.key_to_char(event.scan_code, False)
                if char and len(char) == 1:
                    self.buffer += char

    def check_and_correct_word(self):
        """Check if the current word needs correction and apply it."""
        current_word = self.buffer.strip()
        if not current_word:
            return
            
        # Check Thai to English mappings
        if current_word in self.thai_to_eng_mappings:
            corrected_word = self.thai_to_eng_mappings[current_word]
            self.apply_correction(current_word, corrected_word)
            logger.info(f"Corrected: '{current_word}' to '{corrected_word}'")
            
        # Check English to Thai mappings
        elif current_word in self.eng_to_thai_mappings:
            corrected_word = self.eng_to_thai_mappings[current_word]
            self.apply_correction(current_word, corrected_word)
            logger.info(f"Corrected: '{current_word}' to '{corrected_word}'")
            
        # If no mapping found, add to recent words
        else:
            self.recent_words.append(current_word)
            if len(self.recent_words) > 20:
                self.recent_words.pop(0)
                
    def apply_correction(self, wrong_word, correct_word):
        """Apply the word correction by simulating backspace and typing."""
        # Delete the wrong word (including the space character)
        for _ in range(len(wrong_word) + 1):
            keyboard.press_and_release('backspace')
            
        # Type the correct word and space
        keyboard.write(correct_word + ' ')
        
        # Reset buffer
        self.buffer = ""

    def run(self):
        """Main application loop."""
        # Register keyboard hook
        keyboard.hook(self.on_key_event)
        
        try:
            # Start the tray icon in a separate thread
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            
            logger.info("SwitchLang started and running in background")
            
            # Main loop
            while self.is_running:
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            # Clean up
            keyboard.unhook_all()
            logger.info("SwitchLang stopped")

if __name__ == "__main__":
    app = SwitchLang()
    app.run()