from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import time
import random

# --- Configuration ---
# Your Google credentials (for the Hats & Ladders login)
GOOGLE_EMAIL = "your-google-email@gmail.com"
GOOGLE_PASSWORD = "your-google-password"

# URLs for Hats & Ladders
login_url = "https://hatsandladders.com/login" # This should still be the initial entry point
dashboard_url = "https://hatsandladders.com/climber/dashboard" 

# Browser options
options = webdriver.ChromeOptions()
# options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# --- Helper Functions (Revised and New) ---

def safe_click(driver, by_type, selector, wait_time=10):
    """Waits for an element to be clickable and clicks it."""
    try:
        element = WebDriverWait(driver, wait_time).until(
            EC.element_to_be_clickable((by_type, selector))
        )
        element.click()
        return True
    except TimeoutException:
        print(f"    Timeout: Element '{selector}' not clickable after {wait_time}s.")
        return False
    except NoSuchElementException:
        print(f"    Error: Element '{selector}' not found.")
        return False
    except WebDriverException as e:
        print(f"    WebDriver Error clicking '{selector}': {e}")
        return False

# ... (Previous safe_send_keys and switch_to_learnosity_iframe functions can remain, or be added if they were removed) ...

def login_to_hats_ladders_with_google(driver, email, password, login_page_url, dashboard_check_url):
    """
    Automates login to Hats & Ladders via the 'Sign in with Google' button.
    """
    print("Navigating to login page...")
    driver.get(login_page_url)
    wait = WebDriverWait(driver, 20)

    try:
        # 1. Find and click the "Sign in with Google" button on Hats & Ladders
        print("Looking for 'Sign in with Google' button...")
        # You'll need to inspect the Hats & Ladders login page to find the exact selector for this button.
        # It might be a button with text "Sign in with Google", or an SVG icon, or a specific class.
        # Example XPath: //button[contains(., 'Sign in with Google')] OR //div[contains(@aria-label, 'Sign in with Google')]
        google_signin_button_selector = (By.XPATH, "//button[contains(., 'Sign in with Google') or contains(., 'Continue with Google')] | //div[contains(@aria-label, 'Sign in with Google')]")
        
        # Wait for and click the Google sign-in button
        if not safe_click(driver, google_signin_button_selector[0], google_signin_button_selector[1]):
            print("Could not find or click 'Sign in with Google' button. Please check selector.")
            return False

        print("Clicked 'Sign in with Google'. Waiting for Google login page...")

        # 2. Wait for Google's login page to load (URL changes to accounts.google.com)
        wait.until(EC.url_contains("accounts.google.com"))
        print("Redirected to Google login page.")

        # 3. Enter Google email
        # Google's email input field usually has an ID like 'identifierId'
        email_input_selector = (By.ID, "identifierId")
        email_field = wait.until(EC.presence_of_element_located(email_input_selector))
        email_field.send_keys(email)
        print("Entered Google email.")

        # Click the "Next" button for email
        # Google's next button often has an ID like 'identifierNext' or 'idp-next'
        email_next_button_selector = (By.ID, "identifierNext")
        if not safe_click(driver, email_next_button_selector[0], email_next_button_selector[1]):
            # Fallback if 'identifierNext' isn't found (sometimes it's a generic button)
            print("Could not find 'identifierNext' button directly. Trying generic next button.")
            email_next_button_selector = (By.XPATH, "//div[@id='emailNext'] | //button[contains(.,'Next')]")
            if not safe_click(driver, email_next_button_selector[0], email_next_button_selector[1]):
                print("Failed to click Google email next button.")
                return False
        
        time.sleep(random.uniform(1, 2)) # Small pause for Google to process email

        # 4. Enter Google password
        # Google's password input field usually has a name like 'password' or ID 'password'
        password_input_selector = (By.NAME, "password")
        password_field = wait.until(EC.presence_of_element_located(password_input_selector))
        password_field.send_keys(password)
        print("Entered Google password.")

        # Click the "Next" button for password
        # Google's next button for password often has an ID like 'passwordNext'
        password_next_button_selector = (By.ID, "passwordNext")
        if not safe_click(driver, password_next_button_selector[0], password_next_button_selector[1]):
            # Fallback if 'passwordNext' isn't found
            print("Could not find 'passwordNext' button directly. Trying generic next button.")
            password_next_button_selector = (By.XPATH, "//div[@id='passwordNext'] | //button[contains(.,'Next')]")
            if not safe_click(driver, password_next_button_selector[0], password_next_button_selector[1]):
                print("Failed to click Google password next button.")
                return False

        print("Clicked Google password next button. Waiting for redirect back to Hats & Ladders...")

        # 5. Wait for redirect back to Hats & Ladders (URL should contain dashboard_check_url)
        wait.until(EC.url_contains(dashboard_check_url))
        print("Successfully redirected back to Hats & Ladders dashboard.")
        
        # Optional: Wait for a dashboard element to be fully loaded
        wait.until(EC.presence_of_element_located((By.XPATH, "//h6[contains(text(), '405 XP')]"))) # Or any other unique dashboard element
        print("Hats & Ladders dashboard fully loaded.")
        return True

    except TimeoutException:
        print("Login process timed out at a critical step. Check selectors or network.")
        return False
    except NoSuchElementException:
        print("Login process failed: An expected element was not found.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during Google login: {e}")
        return False

# --- (Other helper functions like switch_to_learnosity_iframe, process_learnosity_activity,
#      and process_module_activities remain the same as in the previous complete script) ---

# --- Main Execution Flow (Revised) ---
if __name__ == "__main__":
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        print("Browser started.")

        # 1. Login using the new Google login function
        if not login_to_hats_ladders_with_google(driver, GOOGLE_EMAIL, GOOGLE_PASSWORD, login_url, dashboard_url):
            print("Google login failed. Exiting.")
            exit()

        # --- Choose your automation path ---
        
        # OPTION 1: Process assignments from the dashboard
        # (This function is from the previous script and assumes you have updated its internal selectors for your dashboard)
        # process_dashboard_assignments(driver) 

        # OPTION 2: Directly go to a specific career climb (uncomment if you prefer this)
        # career_climb_test_url = "https://hatsandladders.com/career-climbs/job-hunt-journey-example-id" # REPLACE WITH REAL URL
        # print(f"\n--- Directly navigating to specific career climb: {career_climb_test_url} ---")
        # driver.get(career_climb_test_url)
        # process_module_activities(driver)


    except Exception as e:
        print(f"\nAn unrecoverable error occurred: {e}")
        if driver:
            driver.save_screenshot("error_screenshot_final.png")
            print("Screenshot saved as error_screenshot_final.png")

    finally:
        if driver:
            print("\nClosing browser...")
            driver.quit()
        print("Program finished.")