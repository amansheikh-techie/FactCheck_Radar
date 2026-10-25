"""Record complete demo video with exact verify-button clicks and full website view."""

import time
import os
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def main():
    out_path = r"g:\nvidia_proj\demo_video.mp4"
    width, height = 1920, 1080
    fps = 15

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument(f"--window-size={width},{height}")
    chrome_options.add_argument("--force-device-scale-factor=1")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--hide-scrollbars")

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(width, height)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

    def snap(repeat=1):
        png = driver.get_screenshot_as_png()
        im = Image.open(BytesIO(png)).convert('RGB')
        im = im.resize((width, height), Image.Resampling.LANCZOS)
        bgr = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)
        for _ in range(repeat):
            video.write(bgr)

    # 1. Homepage initial view
    print("1. Opening FactCheck Radar...")
    driver.get("http://127.0.0.1:8000")
    time.sleep(2)
    snap(fps * 3)

    # ══════════════════════════════════════════════════════════
    # QUERY 1: FALSE CLAIM (Myth)
    # ══════════════════════════════════════════════════════════
    claim1 = "The Great Wall of China is visible from space with the naked eye."
    textarea = driver.find_element(By.ID, "claim-input")
    textarea.clear()
    snap(fps // 2)

    print("2. Typing Claim 1:", claim1)
    for char in claim1:
        textarea.send_keys(char)
        snap(1)
    snap(fps)

    # Click the explicit "verify-button"
    print("3. Pressing Verify Claim button...")
    verify_btn = driver.find_element(By.ID, "verify-button")
    verify_btn.click()
    snap(fps) # show "Investigating..." active state

    print("4. Streaming live progress timeline for Claim 1...")
    start_time = time.time()
    while time.time() - start_time < 8.0:
        snap(1)
        time.sleep(0.06)

    print("5. Viewing Claim 1 FALSE verdict...")
    snap(fps * 2)
    for offset in range(100, 520, 25):
        driver.execute_script(f"window.scrollTo(0, {offset});")
        snap(2)
    snap(fps * 4) # 4 seconds on FALSE verdict, 96% meter, NASA citations

    # ══════════════════════════════════════════════════════════
    # QUERY 2: TRUE CLAIM (Scientific)
    # ══════════════════════════════════════════════════════════
    print("6. Scrolling up for Claim 2...")
    for offset in range(500, -1, -35):
        driver.execute_script(f"window.scrollTo(0, {offset});")
        snap(1)
    snap(fps)

    claim2 = "Water boils at 100 degrees Celsius at standard atmospheric pressure."
    textarea = driver.find_element(By.ID, "claim-input")
    textarea.clear()
    snap(fps // 2)

    print("7. Typing Claim 2 (True):", claim2)
    for char in claim2:
        textarea.send_keys(char)
        snap(1)
    snap(fps)

    # Click the explicit "verify-button"
    print("8. Pressing Verify Claim button...")
    verify_btn = driver.find_element(By.ID, "verify-button")
    verify_btn.click()
    snap(fps) # show "Investigating..." active state

    print("9. Streaming live progress timeline for Claim 2...")
    start_time = time.time()
    while time.time() - start_time < 8.0:
        snap(1)
        time.sleep(0.06)

    print("10. Viewing Claim 2 TRUE verdict...")
    snap(fps * 2)
    for offset in range(100, 520, 25):
        driver.execute_script(f"window.scrollTo(0, {offset});")
        snap(2)
    snap(fps * 4) # 4 seconds on green TRUE verdict, 100% confidence, NIST citations

    # ══════════════════════════════════════════════════════════
    # FULL WEBSITE PANORAMIC VIEW (Light & Dark Mode)
    # ══════════════════════════════════════════════════════════
    print("11. Switching to Dark Mode...")
    theme_btn = driver.find_element(By.CSS_SELECTOR, "header button")
    theme_btn.click()
    time.sleep(0.5)
    snap(fps * 3) # show dark mode result

    print("12. Giving a complete panoramic scroll of the website...")
    # Scroll smoothly through the entire page from top to bottom
    driver.execute_script("window.scrollTo(0, 0);")
    snap(fps * 2)

    # Scroll through Hero & Input
    for offset in range(0, 400, 25):
        driver.execute_script(f"window.scrollTo(0, {offset});")
        snap(2)

    # Scroll through Result Card & Citations
    for offset in range(400, 800, 25):
        driver.execute_script(f"window.scrollTo(0, {offset});")
        snap(2)
    snap(fps * 3)

    # Scroll through How It Works architecture section
    for offset in range(800, 1300, 30):
        driver.execute_script(f"window.scrollTo(0, {offset});")
        snap(2)
    snap(fps * 3) # pause on How It Works in Dark Mode

    # Scroll back up and toggle back to light mode
    print("13. Toggling back to Light Mode...")
    for offset in range(1300, -1, -50):
        driver.execute_script(f"window.scrollTo(0, {offset});")
        snap(1)
    
    theme_btn.click()
    time.sleep(0.5)
    snap(fps * 3) # final view

    driver.quit()
    video.release()
    print("Video rendered successfully to:", out_path)
    print("File size:", os.path.getsize(out_path), "bytes")

if __name__ == "__main__":
    main()
