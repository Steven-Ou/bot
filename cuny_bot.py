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


def select_custom_dropdown(driver, label_text, option_text):
    """Opens the dropdown, filters the huge list, scrolls to the option, and clicks it."""
    print(f"Setting {label_text} to {option_text}...")

    try:
        # 1. Find the exact text label and lock it in the center of the screen
        label = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    f"//*[text()='{label_text}' or normalize-space(text())='{label_text}']",
                )
            )
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", label)
        time.sleep(1)

        # 2. Open the dropdown menu (Targets the box directly next to the label)
        try:
            dropdown_container = label.find_element(
                By.XPATH, "./following-sibling::*[1]"
            )
            driver.execute_script("arguments[0].click();", dropdown_container)
        except Exception:
            # Fallback if structure changes: move down 50 pixels to clear all padding
            actions = ActionChains(driver)
            actions.move_to_element(label).move_by_offset(0, 50).click().perform()

        print("Waiting for the massive dropdown list to appear...")
        time.sleep(2.5)  # Critical wait for the huge list to fetch and render

        # 3. Type the option to filter the list instantly
        print(f"Typing '{option_text}' to filter the list...")
        actions = ActionChains(driver)
        actions.send_keys(option_text).perform()
        time.sleep(2)  # Give the UI time to update the list

        # 4. Scroll down the huge list and explicitly click the text
        print(f"Scrolling down to click '{option_text}'...")
        options = driver.find_elements(
            By.XPATH,
            f"//*[text()='{option_text}' or normalize-space(text())='{option_text}']",
        )

        success = False
        for opt in options:
            try:
                # Make sure we don't accidentally click the original label again
                if opt != label and opt.tag_name.lower() not in ["input"]:
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});", opt
                    )
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", opt)
                    success = True
                    break
            except Exception:
                continue

        # 5. Ultimate Fallback: Just hit Enter to select the filtered option
        if not success:
            print("Could not explicitly click, pressing ENTER key...")
            actions = ActionChains(driver)
            actions.send_keys(Keys.ENTER).perform()

        time.sleep(1.5)

    except Exception as e:
        raise Exception(f"Failed to set {label_text}. Error: {e}")


def check_all_classes():
    chrome_options = Options()
    # Remove the '#' below once you verify the bot runs successfully from start to finish
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=chrome_options)

    try:
        for course in COURSES_TO_CHECK:
            course_num = course["number"]
            target_prof = course["target_professor"]

            print(f"\n--- Checking {SUBJECT_NAME} {course_num} ---")

            driver.get("https://globalsearch.cuny.edu/CFGlobalSearchTool/search.jsp")

            # 1. Select Institution
            inst_checkbox = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//label[contains(text(), '{INSTITUTION_NAME}')]")
                )
            )
            driver.execute_script("arguments[0].click();", inst_checkbox)

            print("Waiting for background data to load...")
            time.sleep(4)

            # 2. Select Term
            select_custom_dropdown(driver, "Term", TERM_NAME)

            # 3. Click Next
            print("Clicking Next...")
            next_btn = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[text()='Next' or contains(text(), 'Next')]")
                )
            )
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", next_btn
            )
            time.sleep(1)
            driver.execute_script("arguments[0].click();", next_btn)

            print("Waiting for Page 2 to initialize...")
            time.sleep(5)

            # 4. Select Subject
            select_custom_dropdown(driver, "Subject", SUBJECT_NAME)

            # 5. Expand Additional Search Criteria
            print("Expanding Search Criteria...")
            try:
                add_criteria = driver.find_element(
                    By.XPATH, "//*[contains(text(), 'Additional Search Criteria')]"
                )
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", add_criteria
                )
                time.sleep(1)
                driver.execute_script("arguments[0].click();", add_criteria)
                time.sleep(1.5)
            except Exception:
                pass

            # 6. Enter Course Number
            print("Entering Course Number...")
            try:
                course_input = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            "//input[@placeholder='Course Number' or contains(@aria-label, 'Course')]",
                        )
                    )
                )
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", course_input
                )
                time.sleep(1)
                course_input.clear()
                course_input.send_keys(course_num)
                time.sleep(1)
            except Exception as e:
                print(f"Warning: Could not enter course number. {e}")

            # 7. Uncheck "Show Open Classes Only"
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

            # 8. Click Search
            print("Clicking Search...")
            search_btn = driver.find_element(
                By.XPATH, "//button[contains(text(), 'Search') or @value='Search']"
            )
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", search_btn
            )
            time.sleep(1)
            driver.execute_script("arguments[0].click();", search_btn)

            # 9. Expand the results container
            print("Waiting for results...")
            try:
                expand_arrow = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//*[contains(text(), 'class section(s) found')]")
                    )
                )
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", expand_arrow
                )
                time.sleep(1)
                driver.execute_script("arguments[0].click();", expand_arrow)
                time.sleep(3)
            except Exception:
                print(f"No classes found for {course_num}.")
                continue

            # 10. Analyze the expanded results
            page_text = driver.find_element(By.TAG_NAME, "body").text

            if target_prof != "" and target_prof.lower() not in page_text.lower():
                print(
                    f"❌ Professor {target_prof} not found in the results for {course_num}. Skipping."
                )
                continue

            prof_label = f"(Prof: {target_prof})" if target_prof else ""
            if "Wait List" in page_text:
                print(f"⚠️ WAITLIST seats available for {course_num}!")
                trigger_notification(
                    f"Waitlist seats found for {SUBJECT_NAME} {course_num}! {prof_label}"
                )
            elif "Open" in page_text and "Closed" not in page_text:
                print(f"🚨 OPEN seats for {course_num}!")
                trigger_notification(
                    f"OPEN seats found for {SUBJECT_NAME} {course_num}! {prof_label}"
                )
            elif "Closed" in page_text:
                print(f"🔒 {course_num} is still closed.")
            else:
                print(f"Status unknown for {course_num}.")

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
