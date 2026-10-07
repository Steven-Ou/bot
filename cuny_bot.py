import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURATION ---
# These MUST match the exact text displayed on the new CUNY UI
INSTITUTION_NAME = "Queens College"
TERM_NAME = "2027 Spring Term"
SUBJECT_NAME = "Computer Science"  # Do not use abbreviations like CSCI
COURSE_NUMBER = "370"
CHECK_INTERVAL = 120
WEBHOOK_URL = "https://discord.com/api/webhooks/1557076166660071518/7nx3NOi714rSf4dbuMheNfvUUjC6o1ksnWCkJHpw83JCSIOzBsqXQR4ZeMiEJFsa73IG"


def check_cuny_class():
    print(f"Checking {SUBJECT_NAME} {COURSE_NUMBER} at {INSTITUTION_NAME}...")

    chrome_options = Options()
    # Remove the '#' below once you verify the bot clicks the right buttons successfully
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # 1. Load the page
        driver.get("https://globalsearch.cuny.edu/CFGlobalSearchTool/search.jsp")

        # 2. Select Institution Checkbox
        print("Selecting Institution...")
        inst_checkbox = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//label[contains(text(), '{INSTITUTION_NAME}')]")
            )
        )
        driver.execute_script("arguments[0].click();", inst_checkbox)
        time.sleep(1)

        # 3. Select Term
        print("Selecting Term...")
        term_dropdown = driver.find_element(
            By.XPATH,
            "//div[contains(text(), 'Term')]/..//div[contains(@class, 'indicatorContainer')] | //div[contains(text(), 'Term')]/following-sibling::div",
        )
        driver.execute_script("arguments[0].click();", term_dropdown)
        time.sleep(1)
        term_option = driver.find_element(
            By.XPATH, f"//*[contains(text(), '{TERM_NAME}')]"
        )
        driver.execute_script("arguments[0].click();", term_option)
        time.sleep(1)

        # 4. Click Next
        print("Clicking Next...")
        next_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Next')]")
        driver.execute_script("arguments[0].click();", next_btn)

        # 5. Select Subject
        print("Selecting Subject...")
        subject_dropdown = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//div[contains(text(), 'Subject')]/..//div[contains(@class, 'indicatorContainer')] | //*[text()='Subject']/following-sibling::*",
                )
            )
        )
        driver.execute_script("arguments[0].click();", subject_dropdown)
        time.sleep(1)
        subject_option = driver.find_element(
            By.XPATH,
            f"//*[text()='{SUBJECT_NAME}'] | //div[contains(text(), '{SUBJECT_NAME}')]",
        )
        driver.execute_script("arguments[0].click();", subject_option)
        time.sleep(1)

        # 6. Expand Additional Search Criteria & Enter Course Number
        print("Entering Course Number...")
        add_criteria = driver.find_element(
            By.XPATH, "//*[contains(text(), 'Additional Search Criteria')]"
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", add_criteria)
        driver.execute_script("arguments[0].click();", add_criteria)
        time.sleep(1)

        # Look for the newly revealed input box based on adjacent text/labels
        course_input = driver.find_element(
            By.XPATH,
            "//input[contains(@name, 'Course') or contains(@aria-label, 'Course') or @placeholder='Course Number' or ../preceding-sibling::*[contains(text(), 'Course Number')]]",
        )
        course_input.send_keys(COURSE_NUMBER)
        time.sleep(1)

        # 7. Uncheck "Show Open Classes Only" Toggle
        print("Toggling 'Open Classes Only' OFF...")
        try:
            toggle = driver.find_element(
                By.XPATH, "//*[contains(text(), 'Show Open Classes Only')]"
            )
            driver.execute_script("arguments[0].click();", toggle)
            time.sleep(1)
        except Exception as e:
            print("Could not flip toggle, moving on...")

        # 8. Click Search
        print("Searching...")
        search_btn = driver.find_element(
            By.XPATH, "//button[contains(text(), 'Search')]"
        )
        driver.execute_script("arguments[0].click();", search_btn)

        # 9. Expand the results container
        print("Waiting for results...")
        expand_arrow = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(), 'class section(s) found')]")
            )
        )
        driver.execute_script("arguments[0].click();", expand_arrow)
        time.sleep(
            3
        )  # Crucial wait time to let the dynamic class data load into the DOM

        # 10. Analyze the expanded results
        page_text = driver.find_element(By.TAG_NAME, "body").text

        if "Wait List" in page_text:
            print("⚠️ ALERT: The class has WAITLIST seats available!")
            trigger_notification("Waitlist seats found!")
        elif "Open" in page_text and "Closed" not in page_text:
            print("🚨 ALERT: The class has OPEN seats!")
            trigger_notification("OPEN seats found!")
        elif "Closed" in page_text:
            print("Class is still closed.")
        else:
            print("Status unknown or class not found.")

    except Exception as e:
        print(f"An error occurred while navigating: {e}")
        driver.save_screenshot("error_screenshot.png")
        print("Saved a fresh error_screenshot.png. Check it to see where it got stuck.")
    finally:
        driver.quit()


def trigger_notification(message):
    print("\a")
    if WEBHOOK_URL != "":
        data = {
            "username": "CUNY Tracker",
            "content": f"🚨 **ALERT!** 🚨\n{message}\nLink: https://globalsearch.cuny.edu/CFGlobalSearchTool/search.jsp",
        }
        try:
            response = requests.post(WEBHOOK_URL, json=data)
            if response.status_code == 204:
                print("✅ Successfully pinged your Discord!")
        except Exception as e:
            print(f"⚠️ Error connecting to Discord: {e}")


if __name__ == "__main__":
    while True:
        check_cuny_class()
        print(f"Sleeping for {CHECK_INTERVAL / 60} minutes...\n")
        time.sleep(CHECK_INTERVAL)
