import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
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
    """Forces clicks on React-based dropdowns instead of typing into hidden inputs."""
    print(f"Setting {label_text} to {option_text}...")

    try:
        # Click the dropdown container to expand the options
        dropdown_container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    f"//*[contains(text(), '{label_text}')]/following-sibling::div | //*[contains(text(), '{label_text}')]/..//div[contains(@class, 'indicatorContainer')]",
                )
            )
        )
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", dropdown_container
        )
        time.sleep(1)
        driver.execute_script("arguments[0].click();", dropdown_container)

        time.sleep(2)  # Give the dropdown menu time to visually open

        # Find the option and click it
        option_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    f"//*[text()='{option_text}' or contains(text(), '{option_text}')]",
                )
            )
        )
        driver.execute_script("arguments[0].click();", option_element)
        time.sleep(1)
    except Exception as e:
        raise Exception(f"Failed to set {label_text}. Error: {e}")


def check_all_classes():
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
        for course in COURSES_TO_CHECK:
            course_num = course["number"]
            target_prof = course["target_professor"]

            print(f"\n--- Checking {SUBJECT_NAME} {course_num} ---")

            # 1. Load the page
            driver.get("https://globalsearch.cuny.edu/CFGlobalSearchTool/search.jsp")

            # 2. Select Institution Checkbox
            inst_checkbox = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//label[contains(text(), '{INSTITUTION_NAME}')]")
                )
            )
            driver.execute_script("arguments[0].click();", inst_checkbox)

            # CRITICAL WAIT: Must allow CUNY's backend time to fetch the terms for this specific institution
            print("Waiting for background data to load...")
            time.sleep(4)

            # 3. Select Term
            select_custom_dropdown(driver, "Term", TERM_NAME)
            time.sleep(1)

            # 4. Click Next
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

            # CRITICAL WAIT: Must allow the second page time to initialize its subject lists
            print("Loading Subject database...")
            time.sleep(4)

            # 5. Select Subject
            select_custom_dropdown(driver, "Subject", SUBJECT_NAME)
            time.sleep(1)

            # 6. Expand Additional Search Criteria & Enter Course Number
            add_criteria = driver.find_element(
                By.XPATH, "//*[contains(text(), 'Additional Search Criteria')]"
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", add_criteria)
            driver.execute_script("arguments[0].click();", add_criteria)
            time.sleep(1)

            course_input = driver.find_element(
                By.XPATH,
                "//input[contains(@name, 'Course') or contains(@aria-label, 'Course') or @placeholder='Course Number' or ../preceding-sibling::*[contains(text(), 'Course Number')]]",
            )
            course_input.send_keys(course_num)
            time.sleep(1)

            # 7. Uncheck "Show Open Classes Only" Toggle
            try:
                toggle = driver.find_element(
                    By.XPATH, "//*[contains(text(), 'Show Open Classes Only')]"
                )
                driver.execute_script("arguments[0].click();", toggle)
                time.sleep(1)
            except Exception:
                pass

            # 8. Click Search
            search_btn = driver.find_element(
                By.XPATH, "//button[contains(text(), 'Search') or @value='Search']"
            )
            driver.execute_script("arguments[0].click();", search_btn)

            # 9. Expand the results container
            try:
                expand_arrow = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//*[contains(text(), 'class section(s) found')]")
                    )
                )
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
        driver.save_screenshot(
            "error_screenshot.png"
        )  # Updated to .png to clear the warning
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
