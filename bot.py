from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import time
import random

# --- Configuration ---
# Your NYC.ID credentials
NYC_ID_USERNAME = "your-nyc-id-username"
NYC_ID_PASSWORD = "your-nyc-id-password"

# URLs for Hats & Ladders
login_url = "https://hatsandladders.com/login" # Initial login page
dashboard_url = "https://hatsandladders.com/climber/dashboard" # Expected URL after successful login

# Browser options (same as before)
options = webdriver.ChromeOptions()
# options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# --- Helper Functions (safe_click, switch_to_learnosity_iframe, process_learnosity_activity,
#      process_module_activities, process_dashboard_assignments are the same as before) ---

# You'll need to include the definitions for:
# - safe_click
# - switch_to_learnosity_iframe
# - process_learnosity_activity
# - process_module_activities
# - process_dashboard_assignments
# from the previous "complete program" section.

def login_to_hats_ladders_with_nyc_id(driver, username, password, login_page_url, dashboard_check_url):
    """
    Automates login to Hats & Ladders via the 'Continue with NYC.ID' button.
    """
    print("Navigating to login page...")
    driver.get(login_page_url)
    wait = WebDriverWait(driver, 20)

    try:
        # 1. Find and click the "Continue with NYC.ID" button on Hats & Ladders
        print("Looking for 'Continue with NYC.ID' button...")
        # *** YOU MUST INSPECT THE HATS & LADDERS LOGIN PAGE TO FIND THE EXACT SELECTOR FOR THIS BUTTON. ***
        # It could be button text, an image, or a specific data-testid.
        # Example: //button[contains(., 'Continue with NYC.ID')]
        nyc_id_signin_button_selector = (By.XPATH, "//button[contains(., 'Continue with NYC.ID')]")
        
        if not safe_click(driver, nyc_id_signin_button_selector[0], nyc_id_signin_button_selector[1]):
            print("Could not find or click 'Continue with NYC.ID' button. Please check selector.")
            return False

        print("Clicked 'Continue with NYC.ID'. Waiting for NYC.ID login page...")

        # 2. Wait for NYC.ID's login page to load (URL will change to NYC.ID's domain)
        # You'll need to know the domain of the NYC.ID login page (e.g., 'login.nyc.gov')
        nyc_id_domain = "login.nyc.gov" # *** REPLACE WITH THE ACTUAL NYC.ID LOGIN DOMAIN ***
        wait.until(EC.url_contains(nyc_id_domain))
        print(f"Redirected to NYC.ID login page ({driver.current_url}).")

        # 3. Enter NYC.ID username/email
        # *** YOU MUST INSPECT THE NYC.ID LOGIN PAGE TO FIND THE EXACT SELECTOR FOR THE USERNAME INPUT. ***
        # It could be by ID, name, or a specific XPath.
        nyc_id_username_input_selector = (By.ID, "nyc-id-username-field") # PLACEHOLDER
        username_field = wait.until(EC.presence_of_element_located(nyc_id_username_input_selector))
        username_field.send_keys(username)
        print("Entered NYC.ID username.")

        # 4. Enter NYC.ID password
        # *** YOU MUST INSPECT THE NYC.ID LOGIN PAGE TO FIND THE EXACT SELECTOR FOR THE PASSWORD INPUT. ***
        nyc_id_password_input_selector = (By.ID, "nyc-id-password-field") # PLACEHOLDER
        password_field = wait.until(EC.presence_of_element_located(nyc_id_password_input_selector))
        password_field.send_keys(password)
        print("Entered NYC.ID password.")
        
        time.sleep(random.uniform(0.5, 1.5)) # Small pause before clicking login

        # 5. Click the NYC.ID login/submit button
        # *** YOU MUST INSPECT THE NYC.ID LOGIN PAGE TO FIND THE EXACT SELECTOR FOR THE LOGIN BUTTON. ***
        nyc_id_login_button_selector = (By.ID, "nyc-id-login-button") # PLACEHOLDER
        if not safe_click(driver, nyc_id_login_button_selector[0], nyc_id_login_button_selector[1]):
            print("Failed to click NYC.ID login button. Please check selector.")
            return False

        print("Clicked NYC.ID login button. Waiting for redirect back to Hats & Ladders...")

        # 6. Wait for redirect back to Hats & Ladders (URL should contain dashboard_check_url)
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
        print(f"An unexpected error occurred during NYC.ID login: {e}")
        return False

# --- Main Execution Flow (Revised) ---
if __name__ == "__main__":
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        print("Browser started.")

        # 1. Login using the new NYC.ID login function
        if not login_to_hats_ladders_with_nyc_id(driver, NYC_ID_USERNAME, NYC_ID_PASSWORD, login_url, dashboard_url):
            print("NYC.ID login failed. Exiting.")
            exit()

        # --- Choose your automation path (as in previous script) ---
        # OPTION 1: Process assignments from the dashboard
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