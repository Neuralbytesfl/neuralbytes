import os
import time
import pyautogui
from PIL import ImageGrab

# Create folder if it doesn't exist
folder_name = "recallv1"
if not os.path.exists(folder_name):
    os.makedirs(folder_name)

def save_screenshot(image, filename):
    # Save screenshot
    image.save(filename)

def compress_image(image, filename):
    # Compress image
    temp_filename = filename + "_temp.png"
    image.save(temp_filename, optimize=True, quality=50)
    compressed_image = Image.open(temp_filename)
    os.remove(temp_filename)
    return compressed_image

def main():
    while True:
        # Capture screenshot using PIL's ImageGrab
        screenshot = ImageGrab.grab()
        timestamp = int(time.time())
        filename = f"{folder_name}/screenshot_{timestamp}.png"
        save_screenshot(screenshot, filename)
        print(f"Screenshot saved: {filename}")
        time.sleep(3)  # Capture every 3 seconds

if __name__ == "__main__":
    main()
