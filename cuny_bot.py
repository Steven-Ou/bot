import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURATION ---
INSTITUTION_NAME = "Queens College"  # EXACT text as it appears in the dropdown
TERM_NAME = "Spring 2027"  # EXACT text as it appears in the dropdown
SUBJECT_VALUE = "CSCI"  # The 3-4 letter subject code (e.g., CSCI, ENGL, MATH)
COURSE_NUMBER = "370"  # The course number
CHECK_INTERVAL = 120  # How often to refresh (in seconds) - Default: 10 mins
WEBHOOK_URL = "https://discord.com/api/webhooks/1557076166660071518/7nx3NOi714rSf4dbuMheNfvUUjC6o1ksnWCkJHpw83JCSIOzBsqXQR4ZeMiEJFsa73IG"

def check_cuny_class():
    print(f"Checking {SUBJECT_VALUE} {COURSE_NUMBER} at {INSTITUTION_NAME}...")

    # Run Chrome in the background (headless)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # 1. Go to CUNY Global Search
        driver.get("https://globalsearch.cuny.edu/CFGlobalSearchTool/search.jsp")

        # 2. Select Institution
        institution = Select(driver.find_element(By.ID, "inst_selection"))
        institution.select_by_visible_text(INSTITUTION_NAME)

        # 3. Select Term
        term = Select(driver.find_element(By.ID, "term_selection"))
        term.select_by_visible_text(TERM_NAME)

        # 4. Click Next
        driver.find_element(By.CLASS_NAME, "ico-next").click()

        # Wait for the next page's subject dropdown to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "subject_selection"))
        )

        # 5. Select Subject
        subject = Select(driver.find_element(By.ID, "subject_selection"))
        subject.select_by_value(SUBJECT_VALUE)

        # 6. Enter Course Number
        driver.find_element(By.ID, "courseNbr").send_keys(COURSE_NUMBER)

        # 7. CRITICAL: Uncheck "Show Open Classes Only" to see Waitlisted/Closed classes
        open_only_checkbox = driver.find_element(By.ID, "open_class_selection")
        if open_only_checkbox.is_selected():
            open_only_checkbox.click()

        # 8. Click Search
        driver.find_element(By.ID, "btnGetClass").click()

        # Wait for results to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "SSSGROUPBOX"))
        )

        # 9. Analyze the results page
        page_source = driver.page_source

        # CUNYfirst uses specific image alt texts for status icons
        if 'alt="Open"' in page_source:
            print("🚨 ALERT: The class has OPEN seats! Go to CUNYfirst now!")
            trigger_notification("OPEN seats found!")
        elif 'alt="Wait List"' in page_source:
            print("⚠️ ALERT: The class has WAITLIST seats available!")
            trigger_notification("Waitlist seats found!")
        elif 'alt="Closed"' in page_source:
            print("Class is still closed.")
        else:
            print("Status unknown or class not found.")

    except Exception as e:
        print(f"An error occurred while navigating: {e}")
    finally:
        driver.quit()


def trigger_notification(message):
    # Plays a local "beep" sound on your computer
    print('\a') 
    
    # Send the notification to your Discord phone/desktop app
    if WEBHOOK_URL != "":
        data = {
            "username": "CUNY Class Tracker",
            "avatar_url": "https://upload.wikimedia.org/wikipedia/en/thumb/e/ed/CUNY_logo.svg/1200px-CUNY_logo.svg.png",
            "content": f"🚨 **ALERT!** 🚨\n{message}\nQuick Link: https://globalsearch.cuny.edu/CFGlobalSearchTool/search.jsp"
        }
        
        try:
            response = requests.post(WEBHOOK_URL, json=data)
            if response.status_code == 204:
                print("✅ Successfully pinged your Discord!")
            else:
                print(f"⚠️ Failed to send Discord notification. Status: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Error connecting to Discord: {e}")
if __name__ == "__main__":
    while True:
        check_cuny_class()
        print(f"Sleeping for {CHECK_INTERVAL / 60} minutes...\n")
        time.sleep(CHECK_INTERVAL)
