import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURATION ---
INSTITUTION_NAME = "Queens College"
TERM_NAME = "2027 Spring Term"
SUBJECT_NAME = "Computer Science"
CHECK_INTERVAL = 120
WEBHOOK_URL = "https://discord.com/api/webhooks/1557076166660071518/7nx3NOi714rSf4dbuMheNfvUUjC6o1ksnWCkJHpw83JCSIOzBsqXQR4ZeMiEJFsa73IG"

COURSES_TO_CHECK = [
    {"number": "370", "target_professor": ""},
    {"number": "381", "target_professor": "Steinberg"},
]

INSTRUCTION_MODES = ["In Person", "Online Synchronous"]


def select_custom_dropdown(driver, label_text, option_text):
    """Restored the robust click/scroll logic that successfully passed steps 1 and 2."""
    print(f"Setting {label_text} to {option_text}...")

    try:
        # 1. Find the exact text label and center it
        label = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//*[normalize-space(text())='{label_text}']")
            )
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", label)
        time.sleep(1)

        # 2. Move mouse just below the label to click the dropdown container
        actions = ActionChains(driver)
        actions.move_to_element(label).move_by_offset(0, 45).click().perform()

        print("Waiting for the massive dropdown list to drop down...")
        time.sleep(2)

        # 3. Type the option to filter the list instantly
        print(f"Typing '{option_text}' to filter the list...")
        actions = ActionChains(driver)
        actions.send_keys(option_text).perform()
        time.sleep(2)

        # 4. Find the filtered option, ensure it is visible, and explicitly click it
        print(f"Scrolling down to click '{option_text}'...")
        options = driver.find_elements(
            By.XPATH,
            f"//*[normalize-space(text())='{option_text}' or contains(text(), '{option_text}')]",
        )

        clicked = False
        for opt in options:
            if opt.is_displayed() and opt.tag_name.lower() not in ["script", "style"]:
                if abs(opt.location["y"] - label.location["y"]) > 10:
                    try:
                        driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});", opt
                        )
                        time.sleep(0.5)
                        driver.execute_script("arguments[0].click();", opt)
                        clicked = True
                        break
                    except:
                        pass

        # 5. Fallback: Hit Enter
        if not clicked:
            print("Could not explicitly click, pressing ENTER key...")
            actions = ActionChains(driver)
            actions.send_keys(Keys.ENTER).perform()

        time.sleep(1.5)

    except Exception as e:
        raise Exception(f"Failed to set {label_text}. Error: {e}")


def check_all_classes():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=chrome_options)

    try:
        print(f"\n--- Starting Master Search for {SUBJECT_NAME} ---")
        driver.get("https://globalsearch.cuny.edu/CFGlobalSearchTool/search.jsp")

        # 1. Select Institution
        inst_checkbox = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//label[contains(text(), '{INSTITUTION_NAME}')]")
            )
        )
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", inst_checkbox
        )
        driver.execute_script("arguments[0].click();", inst_checkbox)

        time.sleep(3)

        # 2. Select Term
        select_custom_dropdown(driver, "Term", TERM_NAME)

        # 3. Click Next
        print("Clicking Next...")
        next_buttons = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//*[normalize-space(text())='Next' or @value='Next']")
            )
        )
        for btn in next_buttons:
            if btn.is_displayed():
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", btn
                )
                time.sleep(1)
                driver.execute_script("arguments[0].click();", btn)
                break

        time.sleep(5)

        # 4. Select Subject
        select_custom_dropdown(driver, "Subject", SUBJECT_NAME)

        # 5. Check "Mode of Instruction" Boxes
        print("Selecting Instruction Modes...")
        for mode in INSTRUCTION_MODES:
            try:
                mode_label = driver.find_element(
                    By.XPATH, f"//label[contains(., '{mode}')]"
                )
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", mode_label
                )
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", mode_label)
                print(f" -> Checked {mode}")
            except Exception:
                print(f" -> Warning: Could not find {mode} checkbox.")

        # 6. Uncheck "Show Open Classes Only"
        print("Toggling 'Open Classes Only' OFF...")
        try:
            toggle = driver.find_element(
                By.XPATH, "//*[contains(text(), 'Show Open Classes Only')]"
            )
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", toggle
            )
            time.sleep(1)
            driver.execute_script("arguments[0].click();", toggle)
            time.sleep(1)
        except Exception:
            pass

        # 7. Click Search
        print("Clicking Search...")
        search_buttons = driver.find_elements(
            By.XPATH, "//*[normalize-space(text())='Search' or @value='Search']"
        )
        for btn in search_buttons:
            if btn.is_displayed():
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", btn
                )
                time.sleep(1)
                driver.execute_script("arguments[0].click();", btn)
                break

        print("Waiting for Master List to load...")
        # Using the exact ID and aria-label revealed in the DevTools screenshot
        expand_arrow = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//a[@id='imageDivLink_inst0' or contains(@aria-label, 'Class Section')]",
                )
            )
        )
        time.sleep(1)

        print("Clicking the arrow to expand the Master List...")
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", expand_arrow
        )
        time.sleep(1)

        # Fire the click exactly on the <a> tag to trigger the expanding javascript
        driver.execute_script("arguments[0].click();", expand_arrow)
        time.sleep(4)
        # 8. Evaluate Each Target Course from the Master List
        print("\n--- Evaluating Target Courses ---")

        for course in COURSES_TO_CHECK:
            course_num = course["number"]
            target_prof = course["target_professor"]

            try:
                print(f"Scanning slowly for {course_num}...")

                # Reset to the top of the page before searching for each course
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1.5)

                course_header = None
                found = False

                # Slowly scroll down like a human (up to 40 times)
                for _ in range(40):
                    try:
                        # Look for the course number on the screen
                        course_header = driver.find_element(
                            By.XPATH,
                            f"//*[contains(text(), ' {course_num} ') or contains(text(), '-{course_num}')]",
                        )

                        # If we find it AND it's physically visible on the screen, stop scrolling!
                        if course_header.is_displayed():
                            print(f"Found {course_num} on screen!")
                            found = True
                            break
                    except:
                        pass  # Not on screen yet, keep scrolling

                    # Scroll down a small amount and wait for the website to load the HTML
                    driver.execute_script("window.scrollBy(0, 400);")
                    time.sleep(1)  # Slow 1-second pause to let React render the classes

                if not found:
                    print(
                        f"❌ {course_num}: Could not locate course in the master list even after scrolling."
                    )
                    continue

                # Center it to be safe before clicking
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", course_header
                )
                time.sleep(1)

                # Click the course header to reveal the table
                driver.execute_script("arguments[0].click();", course_header)
                time.sleep(2)

                # Scrape the specific table that appears underneath the header
                course_table = course_header.find_element(
                    By.XPATH, "./following::table[1]"
                )
                table_text = course_table.text

                if target_prof != "" and target_prof.lower() not in table_text.lower():
                    print(
                        f"❌ {course_num}: Professor '{target_prof}' not found. Skipping."
                    )
                    continue

                prof_label = f"(Prof: {target_prof})" if target_prof else ""

                if "Wait List" in table_text:
                    print(f"⚠️ WAITLIST seats available for {course_num}!")
                    trigger_notification(
                        f"Waitlist seats found for {SUBJECT_NAME} {course_num}! {prof_label}"
                    )
                elif "Open" in table_text and "Closed" not in table_text:
                    print(f"🚨 OPEN seats for {course_num}!")
                    trigger_notification(
                        f"OPEN seats found for {SUBJECT_NAME} {course_num}! {prof_label}"
                    )
                elif "Closed" in table_text:
                    print(f"🔒 {course_num}: Sections are Closed.")
                else:
                    print(f"❓ {course_num}: Status unknown.")

            except Exception as e:
                print(f"❌ {course_num}: Error during evaluation. {e}")

    except Exception as e:
        print(f"An error occurred while navigating: {e}")
        driver.save_screenshot("error_screenshot.png")
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
        check_all_classes()
        print(f"\nSleeping for {CHECK_INTERVAL / 60} minutes...\n")
        time.sleep(CHECK_INTERVAL)
