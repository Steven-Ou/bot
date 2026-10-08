import time
import requests
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()

# --- CONFIGURATION ---
INSTITUTION_NAME = "Queens College"
TERM_NAME = "2027 Spring Term"
SUBJECT_NAME = "Computer Science"
CHECK_INTERVAL = 120
WEBHOOK_URL = os.getenv("CUNY_WEBHOOK_URL")

COURSES_TO_CHECK = [
    {"number": "370", "target_professor": ""},
    {"number": "381", "target_professor": "Steinberg"},
]

INSTRUCTION_MODES = ["In Person", "Online Synchronous"]


def select_custom_dropdown(driver, label_text, option_text):
    print(f"Setting {label_text} to {option_text}...")
    try:
        label = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//*[normalize-space(text())='{label_text}']")
            )
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", label)
        time.sleep(1)

        actions = ActionChains(driver)
        actions.move_to_element(label).move_by_offset(0, 45).click().perform()
        time.sleep(2)

        print(f"Typing '{option_text}' to filter the list...")
        actions = ActionChains(driver)
        actions.send_keys(option_text).perform()
        time.sleep(2)

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

        if not clicked:
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
        expand_arrow = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//a[contains(@id, 'imageDivLink') or contains(@aria-label, 'Class Section')]",
                )
            )
        )

        print("Clicking the arrow to expand the Master List...")
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", expand_arrow
        )
        time.sleep(1)
        driver.execute_script("arguments[0].click();", expand_arrow)

        print("Waiting for the massive class folder to open...")
        content_div = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@id, 'contentDivImg')]")
            )
        )
        time.sleep(3)

        print("\n--- Evaluating Target Courses (Direct Targeting) ---")

        for course in COURSES_TO_CHECK:
            course_num = course["number"]
            target_prof = course["target_professor"]

            try:
                print(f"-> Targeting '{course_num}' in the DOM...")
                elements = content_div.find_elements(
                    By.XPATH, f".//*[contains(., '{course_num}')]"
                )

                target_header = None
                header_title = ""

                for el in reversed(elements):
                    text = driver.execute_script(
                        "return arguments[0].textContent;", el
                    ).strip()
                    if course_num in text and 0 < len(text) < 150:
                        target_header = el
                        header_title = text
                        break

                if not target_header:
                    print(
                        f"❌ ERROR: Could not find '{course_num}' in the Master List code."
                    )
                    continue

                print(f"✅ Found '{header_title}'! Scrolling directly to it...")
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", target_header
                )
                time.sleep(1.5)

                print(f"Clicking to open its table...")
                driver.execute_script("arguments[0].click();", target_header)
                time.sleep(3)  # Ensure the server has time to fetch the class rows

                try:
                    course_table = target_header.find_element(
                        By.XPATH, "./following::table[1]"
                    )

                    # 1. Grab visible text for the Professor check
                    table_text = course_table.text

                    # 2. Grab RAW HTML to read the hidden image tags for Open/Closed/Waitlist indicators
                    table_html = course_table.get_attribute("outerHTML")

                    if (
                        target_prof != ""
                        and target_prof.lower() not in table_text.lower()
                    ):
                        print(
                            f"❌ {course_num}: Professor '{target_prof}' not found. Skipping."
                        )
                        continue

                    prof_label = f"(Prof: {target_prof})" if target_prof else ""

                    # Check the RAW HTML for the image alt tags or titles
                    if "Wait List" in table_html or "Wait List" in table_text:
                        print(f"⚠️ WAITLIST seats available for {course_num}!")
                        trigger_notification(
                            f"Waitlist seats found for {SUBJECT_NAME} {course_num}! {prof_label}"
                        )
                    elif (
                        'alt="Open"' in table_html
                        or 'title="Open"' in table_html
                        or 'aria-label="Open"' in table_html
                        or "Open" in table_text
                    ):
                        print(f"🚨 OPEN seats for {course_num}!")
                        trigger_notification(
                            f"OPEN seats found for {SUBJECT_NAME} {course_num}! {prof_label}"
                        )
                    elif (
                        'alt="Closed"' in table_html
                        or 'title="Closed"' in table_html
                        or 'aria-label="Closed"' in table_html
                        or "Closed" in table_text
                    ):
                        print(f"🔒 {course_num}: Sections are Closed.")
                    else:
                        print(
                            f"❓ {course_num}: Status unknown. Raw HTML snippet: {table_html[:150]}..."
                        )

                except Exception as e:
                    print(
                        f"❌ ERROR: Opened '{course_num}' but couldn't read the class table. {e}"
                    )

            except Exception as e:
                print(f"❌ ERROR: Crash while processing {course_num}. {e}")

    except Exception as e:
        print(f"An error occurred while navigating: {e}")
        driver.save_screenshot("error_screenshot.png")
    finally:
        driver.quit()


def trigger_notification(message):
    print("\a")
    if WEBHOOK_URL and WEBHOOK_URL.startswith("http"):
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
    else:
        print(
            "⚠️ Discord Webhook not sent: WEBHOOK_URL is missing or invalid in your .env file."
        )


if __name__ == "__main__":
    while True:
        check_all_classes()
        print(f"\nSleeping for {CHECK_INTERVAL / 60} minutes...\n")
        time.sleep(CHECK_INTERVAL)
