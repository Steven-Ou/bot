from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import time
import random
import os
from dotenv import load_dotenv # For loading credentials from .env file

# Load environment variables from .env file
load_dotenv()

# --- Configuration (Loaded from .env) ---
AUTH_METHOD = os.getenv("AUTH_METHOD", "google") # 'google', 'nyc_id', or 'direct'
GOOGLE_EMAIL = os.getenv("GOOGLE_EMAIL")
GOOGLE_PASSWORD = os.getenv("GOOGLE_PASSWORD")
NYC_ID_USERNAME = os.getenv("NYC_ID_USERNAME")
NYC_ID_PASSWORD = os.getenv("NYC_ID_PASSWORD")
NYC_ID_LOGIN_DOMAIN = os.getenv("NYC_ID_LOGIN_DOMAIN", "login.nyc.gov") # Default, but verify!
DIRECT_EMAIL = os.getenv("DIRECT_EMAIL")
DIRECT_PASSWORD = os.getenv("DIRECT_PASSWORD")

# Optional: Specific career climb URL for direct testing (uncomment in main to use)
CAREER_CLIMB_TEST_URL = os.getenv("CAREER_CLIMB_TEST_URL")

# General URLs for Hats & Ladders
LOGIN_URL = "https://hatsandladders.com/login"
DASHBOARD_URL = "https://hatsandladders.com/climber/dashboard"

# Browser options
options = webdriver.ChromeOptions()
# options.add_argument("--headless") # Uncomment to run without a visible browser window
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080") # Set a consistent window size
options.add_argument("--no-sandbox") # Required for some environments (e.g., Docker)
options.add_argument("--disable-dev-shm-usage") # Overcomes limited resource problems

# --- Helper Functions ---

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

def safe_send_keys(driver, by_type, selector, text, wait_time=10):
    """Waits for an element to be present and sends keys to it."""
    try:
        element = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((by_type, selector))
        )
        element.send_keys(text)
        return True
    except TimeoutException:
        print(f"    Timeout: Element '{selector}' not found for sending keys after {wait_time}s.")
        return False
    except NoSuchElementException:
        print(f"    Error: Element '{selector}' not found for sending keys.")
        return False
    except WebDriverException as e:
        print(f"    WebDriver Error sending keys to '{selector}': {e}")
        return False

def switch_to_learnosity_iframe(driver, wait_time=20):
    """Waits for and switches to the Learnosity iframe."""
    try:
        # Prioritize finding by ID if known, otherwise by src.
        # This XPath tries to find an iframe with learnosity.com in its src,
        # but specifically excludes the 'x-origin-frame' used for cross-domain communication.
        iframe_selector = (By.XPATH, "//iframe[contains(@src, 'learnosity.com') and not(contains(@class, 'x-origin-frame'))]")
        
        WebDriverWait(driver, wait_time).until(
            EC.frame_to_be_available_and_switch_to_it(iframe_selector)
        )
        print("    Switched to Learnosity iframe.")
        return True
    except TimeoutException:
        print("    Timeout: Learnosity iframe not found or not available within the given time.")
        return False
    except Exception as e:
        print(f"    Error switching to Learnosity iframe: {e}")
        return False

def process_learnosity_activity(driver, wait_time=15):
    """
    Handles an activity *inside* the Learnosity iframe.
    This is the most complex part and requires detailed inspection of Learnosity's HTML.
    """
    print("    Processing activity within Learnosity iframe...")
    try:
        # --- IMPORTANT: You need to customize these selectors based on actual Learnosity content ---
        
        # Scenario 1: Quiz (Multiple Choice/Radio Button/Checkbox)
        try:
            # Look for common quiz question containers or question types within Learnosity
            quiz_question_container = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'lrn-question') or contains(@class, 'lrn-multiplechoice') or contains(@class, 'lrn-checkbox')]"))
            )
            print("    Detected Quiz activity.")
            
            # Find all possible answer options (e.g., radio buttons or checkboxes' labels)
            # This is a very generic XPath; adapt based on actual HTML. Look for input[type='radio/checkbox'] parents.
            answer_options = quiz_question_container.find_elements(By.XPATH, ".//input[@type='radio' or @type='checkbox']/ancestor::label | .//div[contains(@class, 'lrn-choice')]")
            
            if answer_options:
                # --- QUIZ ANSWER LOGIC ---
                # This is where your "cheat" logic would go.
                # 1. Scrape the question: e.g., quiz_question_container.find_element(By.CLASS_NAME, "lrn-question-label").text
                # 2. Scrape options text: [opt.text for opt in answer_options]
                # 3. Implement logic to choose the correct answer. Examples:
                #    - Lookup in a predefined dictionary (question -> answer).
                #    - Use an LLM API to get an answer (advanced).
                #    - For simple testing/skipping: pick the first or a random one.
                
                # Current simple strategy: Pick the first available option
                selected_option = answer_options[0] 
                print(f"    Selecting answer: '{selected_option.text if selected_option.text else '(no visible text)'}'")
                selected_option.click() # Click the label or the clickable part of the option

                time.sleep(random.uniform(1, 2)) # Simulate reading/thinking time
                
                # Find and click the Learnosity submit/next button within the iframe
                # Common Learnosity button classes include 'lrn-button', 'lrn-save-button', etc.
                submit_button_selector = (By.XPATH, "//*[contains(@class, 'lrn-button') or contains(@class, 'lrn-save-button') or contains(text(), 'Submit') or contains(text(), 'Next') or contains(text(), 'Check Answer')]")
                if safe_click(driver, submit_button_selector[0], submit_button_selector[1], wait_time=5):
                    print("    Quiz answer submitted.")
                    return True
                else:
                    print("    Could not find submit button for quiz.")
                    return False
            else:
                print("    No answer options found for quiz.")
                return False

        except TimeoutException:
            # Not a quiz, try other types
            pass
        
        # Scenario 2: Reflection Prompt (Text Area)
        try:
            reflection_textarea_selector = (By.XPATH, "//textarea[contains(@class, 'lrn-text-input') or @aria-label='Reflection response' or @placeholder='Your answer']")
            reflection_textarea = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located(reflection_textarea_selector)
            )
            print("    Detected Reflection activity.")
            
            # Pre-defined response (customize this!) or generate one
            reflection_text = "This is an automated response to the reflection prompt. I found the content insightful and will apply these learnings to my career path."
            reflection_textarea.send_keys(reflection_text)
            print("    Reflection text entered.")
            
            time.sleep(random.uniform(1, 2)) # Simulate typing time
            
            # Find and click the Learnosity submit button
            submit_button_selector = (By.XPATH, "//*[contains(@class, 'lrn-button') or contains(text(), 'Submit') or contains(text(), 'Done')]")
            if safe_click(driver, submit_button_selector[0], submit_button_selector[1], wait_time=5):
                print("    Reflection submitted.")
                return True
            else:
                print("    Could not find submit button for reflection.")
                return False
        except TimeoutException:
            # Not a reflection, try other types
            pass
            
        # Scenario 3: Video or Passive Content (Just wait for it to finish or for a 'continue' button)
        try:
            video_player_selector = (By.XPATH, "//*[contains(@class, 'lrn-video-player') or contains(@class, 'lrn-activity-video')]")
            video_player = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located(video_player_selector)
            )
            print("    Detected Video/Passive content. Waiting for estimated duration...")
            # For simplicity, wait a fixed time. In a real scenario, you might parse video duration or look for a 'skip' button.
            time.sleep(random.uniform(8, 15)) # Simulate watching video
            
            # After video, look for a "Continue" or "Next" button within the iframe
            continue_button_selector = (By.XPATH, "//*[contains(@class, 'lrn-button') or contains(text(), 'Continue') or contains(text(), 'Next') or contains(text(), 'Done')]")
            if safe_click(driver, continue_button_selector[0], continue_button_selector[1], wait_time=5):
                print("    Video/Passive content 'Continue' button clicked.")
                return True
            else:
                print("    Could not find 'Continue' button after video. Assuming auto-proceed or end of passive content.")
                return False # Still return False as we didn't explicitly finish
        except TimeoutException:
            print("    No explicit Video/Passive content detected. Trying generic submission.")
            # If none of the specific scenarios matched, try a generic submit/next button.
            try:
                generic_submit_button_selector = (By.XPATH, "//*[contains(@class, 'lrn-button') or contains(text(), 'Submit') or contains(text(), 'Next') or contains(text(), 'Done')]")
                if safe_click(driver, generic_submit_button_selector[0], generic_submit_button_selector[1], wait_time=5):
                    print("    Clicked generic Learnosity 'Next/Submit/Done' button.")
                    return True
                else:
                    print("    No generic 'Next/Submit/Done' button found in Learnosity. Stuck on this activity.")
                    return False
            except Exception as e:
                print(f"    Error trying generic submit in Learnosity: {e}")
                return False
    except Exception as e:
        print(f"    An unexpected error occurred during Learnosity activity processing: {e}")
        return False
    
    return False # If none of the scenarios matched or completed successfully

def process_module_activities(driver):
    """
    Automates clicking through activities within a specific learning module (e.g., Career Climb).
    Assumes already on the module's main page.
    """
    print("\n--- Starting module activity processing ---")
    wait = WebDriverWait(driver, 20)
    processed_activities_count = 0

    while True:
        time.sleep(random.uniform(2, 4)) # Small pause for page stability
        
        try:
            # Find the "Next" button for the overall module navigation.
            # This button moves to the next activity tile or overall module completion.
            # Based on your HTML, it's often a right-arrow icon button in the main page content.
            # The XPath targets a button with a right arrow icon (eva-arrow-ios-forward-outline).
            module_next_button_selector = (By.XPATH, "//button[contains(@class, 'MuiIconButton-root') and .//*[name()='svg' and @data-icon='eva-arrow-ios-forward-outline']]")
            
            if not safe_click(driver, module_next_button_selector[0], module_next_button_selector[1]):
                print("No more module navigation 'Next' buttons found or button not clickable. Assumed all activities in module completed or process ended.")
                break # Exit the loop if no more next buttons are found
            
            print(f"Clicked module navigation 'Next' button. (Activity {processed_activities_count + 1})")
            processed_activities_count += 1
            time.sleep(random.uniform(3, 5)) # Wait for the new activity to load, possibly iframe

            # Now, attempt to handle the Learnosity iframe for the current activity
            if switch_to_learnosity_iframe(driver):
                if process_learnosity_activity(driver):
                    print("    Activity in iframe successfully processed.")
                else:
                    print("    Failed to process activity in iframe.")
                
                # Always switch back to the main content after trying to handle the iframe
                driver.switch_to.default_content()
                print("    Switched back to main page after iframe processing.")
            else:
                print("    No Learnosity iframe detected for this activity. Assuming main page interaction or completion.")
                # If no iframe, maybe it's just a page refresh or completion confirmation?
                # You might need to add specific logic here if some activities are not in iframes.
                
            time.sleep(random.uniform(2, 3)) # Pause before looking for the next module button

        except TimeoutException:
            print("No more module navigation 'Next' buttons found. Assumed all activities in module completed or process ended.")
            break # Exit the loop if no more next buttons are found
        except NoSuchElementException:
            print("Module 'Next' button not found. May have reached end of module or page changed.")
            break
        except Exception as e:
            print(f"An unexpected error occurred during module processing: {e}")
            break
    
    print(f"--- Module activity processing finished. Processed {processed_activities_count} activities. ---")


def process_dashboard_assignments(driver):
    """
    Navigates to the dashboard and attempts to process available assignments.
    """
    print("\n--- Navigating to Dashboard to check assignments ---")
    driver.get(DASHBOARD_URL)
    wait = WebDriverWait(driver, 15)
    
    try:
        # Wait for a known element on the dashboard indicating it's loaded
        wait.until(EC.presence_of_element_located((By.XPATH, "//h6[contains(text(), 'My Assignments')] | //h3[contains(text(), 'Dashboard')]")))
        print("Landed on dashboard.")

        # --- IMPORTANT: Customize these selectors for your dashboard's assignment list ---
        # Look for elements that represent individual assignments.
        # Example: Find all div elements with a specific class that wraps each assignment
        # You'll need to inspect your live dashboard HTML for these selectors!
        # This XPath is a guess based on the HTML snippet you provided previously.
        assignment_list_items_selector = (By.XPATH, "//div[contains(@class, 'MuiBox-root') and .//h6[contains(text(), 'My Assignments')]]/following-sibling::div[contains(@class, 'MuiStack-root')]//div[contains(@class, 'MuiBox-root')]")
        
        assignment_list_items = driver.find_elements(assignment_list_items_selector[0], assignment_list_items_selector[1])
        
        if not assignment_list_items:
            print("No assignments found on the dashboard or couldn't locate assignment elements.")
            return
            
        print(f"Found {len(assignment_list_items)} potential assignments.")

        for i, assignment_item in enumerate(assignment_list_items):
            try:
                # Find the title of the assignment within its item block
                assignment_title_element = assignment_item.find_element(By.XPATH, ".//h6")
                assignment_title = assignment_title_element.text if assignment_title_element else f"Unknown Assignment {i+1}"
                
                # Find the link or button to start/continue this specific assignment
                # This could be an <a> tag, or a <button> with a right arrow icon.
                # Inspect your dashboard for the correct selector.
                start_button_selector = (By.XPATH, ".//button[contains(@class, 'MuiButtonBase-root')]") # Or a more specific XPath for the 'start' button
                
                print(f"\nProcessing Dashboard Assignment: {assignment_title}")
                
                # Click the assignment to navigate to its module page
                if not safe_click(driver, start_button_selector[0], start_button_selector[1]):
                    print(f"    Failed to click start button for assignment: '{assignment_title}'. Skipping.")
                    continue # Try next assignment if this one can't be clicked
                
                print(f"    Clicked to open assignment: '{assignment_title}'")
                time.sleep(random.uniform(4, 6)) # Wait for the assignment page to load

                # Once on the assignment's module page, use the existing module processing logic
                process_module_activities(driver)
                
                # After completing a module, the page might return to the dashboard
                # or stay on a completion screen. You might need to explicitly go back
                # to the dashboard to find the next assignment.
                print("    Returning to dashboard to check for next assignment...")
                driver.get(DASHBOARD_URL)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//h6[contains(text(), 'My Assignments')] | //h3[contains(text(), 'Dashboard')]")))
                time.sleep(2) # Give it a moment to refresh the assignment list

            except NoSuchElementException:
                print(f"    Could not find title or start button for dashboard assignment item {i+1}. Skipping.")
            except Exception as e:
                print(f"    An error occurred while trying to open/process dashboard assignment {assignment_title}: {e}")
                # Try to navigate back to dashboard to continue with other assignments
                try:
                    driver.get(DASHBOARD_URL)
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//h6[contains(text(), 'My Assignments')] | //h3[contains(text(), 'Dashboard')]")))
                except:
                    print("    Failed to return to dashboard after error. Exiting assignment processing.")
                    return # Exit if we can't get back to dashboard

    except TimeoutException:
        print("Dashboard page did not load or assignments section not found.")
    except Exception as e:
        print(f"An unexpected error occurred during dashboard assignment processing: {e}")

def login_to_hats_ladders(driver, auth_method):
    """
    Handles login based on the specified authentication method.
    """
    driver.get(LOGIN_URL)
    wait = WebDriverWait(driver, 20)

    if auth_method == "google":
        print(f"Attempting login with Google ({GOOGLE_EMAIL})...")
        if not GOOGLE_EMAIL or not GOOGLE_PASSWORD:
            raise ValueError("Google credentials (GOOGLE_EMAIL, GOOGLE_PASSWORD) not set in .env")

        # 1. Click 'Sign in with Google' button on Hats & Ladders
        google_signin_button_selector = (By.XPATH, "//button[contains(., 'Sign in with Google') or contains(., 'Continue with Google')] | //div[contains(@aria-label, 'Sign in with Google')]")
        if not safe_click(driver, google_signin_button_selector[0], google_signin_button_selector[1]):
            raise Exception("Failed to click 'Sign in with Google' button on Hats & Ladders login page.")
        
        print("Clicked 'Sign in with Google'. Waiting for Google login page...")
        wait.until(EC.url_contains("accounts.google.com"))
        print("Redirected to Google login page.")

        # 2. Enter Google email
        if not safe_send_keys(driver, By.ID, "identifierId", GOOGLE_EMAIL):
            raise Exception("Failed to enter Google email.")
        
        # Click the "Next" button for email
        email_next_button_selector = (By.ID, "identifierNext")
        if not safe_click(driver, email_next_button_selector[0], email_next_button_selector[1]):
            # Fallback if 'identifierNext' isn't found (sometimes it's a generic button)
            print("    Could not find 'identifierNext' button directly. Trying generic Google next button.")
            email_next_button_selector = (By.XPATH, "//div[@id='emailNext'] | //button[contains(.,'Next')]")
            if not safe_click(driver, email_next_button_selector[0], email_next_button_selector[1]):
                raise Exception("Failed to click Google email next button.")
        
        time.sleep(random.uniform(1, 2)) # Small pause for Google to process email

        # 3. Enter Google password
        password_input_selector = (By.NAME, "password") # Or By.ID, "password"
        if not safe_send_keys(driver, password_input_selector[0], password_input_selector[1], GOOGLE_PASSWORD):
            raise Exception("Failed to enter Google password.")

        # Click the "Next" button for password
        password_next_button_selector = (By.ID, "passwordNext")
        if not safe_click(driver, password_next_button_selector[0], password_next_button_selector[1]):
            # Fallback if 'passwordNext' isn't found
            print("    Could not find 'passwordNext' button directly. Trying generic Google next button.")
            password_next_button_selector = (By.XPATH, "//div[@id='passwordNext'] | //button[contains(.,'Next')]")
            if not safe_click(driver, password_next_button_selector[0], password_next_button_selector[1]):
                raise Exception("Failed to click Google password next button.")

        print("Clicked Google password next button. Waiting for redirect back to Hats & Ladders...")
        wait.until(EC.url_contains(DASHBOARD_URL))
        print("Successfully redirected back to Hats & Ladders dashboard.")

    elif auth_method == "nyc_id":
        print(f"Attempting login with NYC.ID ({NYC_ID_USERNAME})...")
        if not NYC_ID_USERNAME or not NYC_ID_PASSWORD:
            raise ValueError("NYC.ID credentials (NYC_ID_USERNAME, NYC_ID_PASSWORD) not set in .env")

        # 1. Click 'Continue with NYC.ID' button on Hats & Ladders
        nyc_id_signin_button_selector = (By.XPATH, "//button[contains(., 'Continue with NYC.ID')]") # VERIFY THIS SELECTOR!
        if not safe_click(driver, nyc_id_signin_button_selector[0], nyc_id_signin_button_selector[1]):
            raise Exception("Failed to click 'Continue with NYC.ID' button on Hats & Ladders login page.")

        print("Clicked 'Continue with NYC.ID'. Waiting for NYC.ID login page...")
        wait.until(EC.url_contains(NYC_ID_LOGIN_DOMAIN))
        print(f"Redirected to NYC.ID login page ({driver.current_url}).")

        # 2. Enter NYC.ID username/email
        # *** YOU MUST INSPECT THE NYC.ID LOGIN PAGE FOR THESE SELECTORS ***
        nyc_id_username_input_selector = (By.ID, "username") # PLACEHOLDER: VERIFY THIS ID!
        if not safe_send_keys(driver, nyc_id_username_input_selector[0], nyc_id_username_input_selector[1], NYC_ID_USERNAME):
            raise Exception("Failed to enter NYC.ID username.")

        # 3. Enter NYC.ID password
        # *** YOU MUST INSPECT THE NYC.ID LOGIN PAGE FOR THESE SELECTORS ***
        nyc_id_password_input_selector = (By.ID, "password") # PLACEHOLDER: VERIFY THIS ID!
        if not safe_send_keys(driver, nyc_id_password_input_selector[0], nyc_id_password_input_selector[1], NYC_ID_PASSWORD):
            raise Exception("Failed to enter NYC.ID password.")
        
        time.sleep(random.uniform(0.5, 1.5))

        # 4. Click the NYC.ID login/submit button
        # *** YOU MUST INSPECT THE NYC.ID LOGIN PAGE FOR THIS SELECTOR ***
        nyc_id_login_button_selector = (By.ID, "loginButton") # PLACEHOLDER: VERIFY THIS ID!
        if not safe_click(driver, nyc_id_login_button_selector[0], nyc_id_login_button_selector[1]):
            raise Exception("Failed to click NYC.ID login button.")

        print("Clicked NYC.ID login button. Waiting for redirect back to Hats & Ladders...")
        wait.until(EC.url_contains(DASHBOARD_URL))
        print("Successfully redirected back to Hats & Ladders dashboard.")

    elif auth_method == "direct":
        print(f"Attempting direct login ({DIRECT_EMAIL})...")
        if not DIRECT_EMAIL or not DIRECT_PASSWORD:
            raise ValueError("Direct login credentials (DIRECT_EMAIL, DIRECT_PASSWORD) not set in .env")

        username_field_selector = (By.NAME, "email")
        password_field_selector = (By.NAME, "password")
        login_button_selector = (By.XPATH, "//button[span[text()='Login']]") # Adjust this XPath if "Login" text changes
        
        if not safe_send_keys(driver, username_field_selector[0], username_field_selector[1], DIRECT_EMAIL):
            raise Exception("Failed to enter direct email.")
        if not safe_send_keys(driver, password_field_selector[0], password_field_selector[1], DIRECT_PASSWORD):
            raise Exception("Failed to enter direct password.")
        
        if not safe_click(driver, login_button_selector[0], login_button_selector[1]):
             # Fallback if the above XPath doesn't work (e.g., button text is not direct span)
             login_button_selector = (By.XPATH, "//button[contains(text(), 'Login')]") # Try with contains
             if not safe_click(driver, login_button_selector[0], login_button_selector[1]):
                 # Last resort: find by a common MUI button class or form submit
                 login_button_selector = (By.XPATH, "//form//button[@type='submit']")
                 if not safe_click(driver, login_button_selector[0], login_button_selector[1]):
                    raise Exception("Failed to find or click direct login button.")
        
        print("Direct login attempt complete. Waiting for dashboard...")
        wait.until(EC.url_contains(DASHBOARD_URL)) # Or a specific element on dashboard
        print("Successfully logged in via direct credentials.")

    else:
        raise ValueError(f"Unsupported authentication method: {auth_method}. Check AUTH_METHOD in .env.")
    
    # Final check for dashboard loading
    wait.until(EC.presence_of_element_located((By.XPATH, "//h6[contains(text(), '405 XP')]"))) # Or any other unique dashboard element
    print("Hats & Ladders dashboard fully loaded and confirmed.")
    return True


# --- Main Execution Flow ---
if __name__ == "__main__":
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        print("Browser started.")

        # Perform login based on AUTH_METHOD specified in .env
        if not login_to_hats_ladders(driver, AUTH_METHOD):
            print("Login failed. Exiting script.")
            exit()

        # --- Choose your automation path here ---
        
        # Option A: Process assignments found on the dashboard
        # This will navigate to the dashboard, find assignments, and process them one by one.
        process_dashboard_assignments(driver)

        # Option B: Directly go to a specific career climb module
        # Uncomment the lines below AND make sure CAREER_CLIMB_TEST_URL is set in your .env
        # if CAREER_CLIMB_TEST_URL:
        #     print(f"\n--- Directly navigating to specific career climb: {CAREER_CLIMB_TEST_URL} ---")
        #     driver.get(CAREER_CLIMB_TEST_URL)
        #     process_module_activities(driver)
        # else:
        #     print("CAREER_CLIMB_TEST_URL not set in .env. Skipping direct career climb navigation.")


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