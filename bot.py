from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains 
from selenium.webdriver.common.keys import Keys 
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, StaleElementReferenceException
import time
import random
import os
from dotenv import load_dotenv 

load_dotenv()

# --- Configuration (Loaded from .env) ---
AUTH_METHOD = os.getenv("AUTH_METHOD", "nyc_id") 

NYC_ID_USERNAME = os.getenv("NYC_ID_USERNAME")
NYC_ID_PASSWORD = os.getenv("NYC_ID_PASSWORD")
NYC_ID_LOGIN_DOMAIN = os.getenv("NYC_ID_LOGIN_DOMAIN", "nyc.id") 
DIRECT_EMAIL = os.getenv("DIRECT_EMAIL")
DIRECT_PASSWORD = os.getenv("DIRECT_PASSWORD")

CAREER_CLIMB_TEST_URL = os.getenv("CAREER_CLIMB_TEST_URL")

LOGIN_URL = "https://authorize.hatsandladders.com/login?client_id=7fpt2ssn7snaolk5bjnat4pagf&response_type=code&redirect_uri=https://app.hatsandladders.com"
DASHBOARD_URL = "https://app.hatsandladders.com/climber/dashboard"

options = webdriver.ChromeOptions()
# options.add_argument("--headless") 
options.add_argument("--disable-gpu") 
options.add_argument("--window-size=1920,1080") 
options.add_argument("--no-sandbox") 
options.add_argument("--disable-dev-shm-usage") 

# --- Helper Functions ---

def safe_click(driver, by_type, selector, wait_time=10):
    """
    Waits for an element to be clickable and attempts to click it using multiple strategies.
    This helps overcome issues with overlays, dynamic content, or complex event listeners.
    """
    try:
        element = WebDriverWait(driver, wait_time).until(
            EC.element_to_be_clickable((by_type, selector))
        )
        try:
            element.click()
            print(f"    Native click successful for '{selector}'.")
            return True
        except (WebDriverException, StaleElementReferenceException) as e:
            print(f"    Native click failed for '{selector}': {e}. Trying JavaScript click...")

            try:
                element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((by_type, selector)))
                driver.execute_script("arguments[0].click();", element)
                print(f"    JavaScript click successful for '{selector}'.")
                return True
            except Exception as js_e:
                print(f"    JavaScript click failed for '{selector}': {js_e}. Trying Actions chain...")

                try:
                    element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((by_type, selector)))
                    ActionChains(driver).move_to_element(element).click().perform()
                    print(f"    Actions chain click successful for '{selector}'.")
                    return True
                except Exception as ac_e:
                    print(f"    Actions chain click failed for '{selector}': {ac_e}. Trying keyboard ENTER...")

                    try:
                        element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((by_type, selector)))
                        element.send_keys(Keys.ENTER)
                        print(f"    Keyboard ENTER successful for '{selector}'.")
                        return True
                    except Exception as k_e:
                        print(f"    Keyboard ENTER failed for '{selector}': {k_e}.")
                        return False 

    except TimeoutException:
        print(f"    Timeout: Element '{selector}' not present or clickable after {wait_time}s.")
        return False
    except NoSuchElementException:
        print(f"    Error: Element '{selector}' not found at all.")
        return False
    except Exception as final_e:
        print(f"    An unexpected error occurred during safe_click for '{selector}': {final_e}")
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
    This is the most complex part and requires **detailed inspection of Learnosity's HTML**
    for each activity type. You will need to customize the selectors and logic below.
    """
    print("    Processing activity within Learnosity iframe...")
    try:
        # --- IMPORTANT: YOU NEED TO CUSTOMIZE THESE SELECTORS AND LOGIC ---
        
        # Scenario 1: Quiz (Multiple Choice/Radio Button/Checkbox)
        try:
            quiz_question_container = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'lrn-question') or contains(@class, 'lrn-multiplechoice') or contains(@class, 'lrn-checkbox')]"))
            )
            print("    Detected Quiz activity.")
            
            answer_options = quiz_question_container.find_elements(By.XPATH, ".//input[@type='radio' or @type='checkbox']/ancestor::label | .//div[contains(@class, 'lrn-choice')]")
            
            if answer_options:
                selected_option = answer_options[0] 
                print(f"    Selecting answer: '{selected_option.text if selected_option.text else '(no visible text)'}'")
                selected_option.click() 

                time.sleep(random.uniform(1, 2)) 
                
                submit_button_selector = (By.XPATH, "//*[contains(@class, 'lrn-button') or contains(@class, 'lrn-save-button') or contains(text(), 'Submit') or contains(text(), 'Next') or contains(text(), 'Check Answer')]")
                if safe_click(driver, submit_button_selector[0], submit_button_selector[1], wait_time=5):
                    print("    Quiz answer submitted.")
                    return True
                else:
                    print("    Could not find submit button for quiz. Manual intervention may be needed.")
                    return False
            else:
                print("    No answer options found for quiz.")
                return False

        except TimeoutException:
            pass
        
        # Scenario 2: Reflection Prompt (Text Area)
        try:
            reflection_textarea_selector = (By.XPATH, "//textarea[contains(@class, 'lrn-text-input') or @aria-label='Reflection response' or @placeholder='Your answer']")
            reflection_textarea = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located(reflection_textarea_selector)
            )
            print("    Detected Reflection activity.")
            
            reflection_text = "This is an automated response to the reflection prompt. I found the content insightful and will apply these learnings to my career path."
            reflection_textarea.send_keys(reflection_text)
            print("    Reflection text entered.")
            
            time.sleep(random.uniform(1, 2)) 
            
            submit_button_selector = (By.XPATH, "//*[contains(@class, 'lrn-button') or contains(text(), 'Submit') or contains(text(), 'Done')]")
            if safe_click(driver, submit_button_selector[0], submit_button_selector[1], wait_time=5):
                print("    Reflection submitted.")
                return True
            else:
                print("    Could not find submit button for reflection. Manual intervention may be needed.")
                return False
        except TimeoutException:
            pass
            
        # Scenario 3: Video or Passive Content (Just wait for it to finish or for a 'continue' button)
        try:
            video_player_selector = (By.XPATH, "//*[contains(@class, 'lrn-video-player') or contains(@class, 'lrn-activity-video')]")
            video_player = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located(video_player_selector)
            )
            print("    Detected Video/Passive content. Waiting for estimated duration...")
            time.sleep(random.uniform(8, 15)) 
            
            continue_button_selector = (By.XPATH, "//*[contains(@class, 'lrn-button') or contains(text(), 'Continue') or contains(text(), 'Next') or contains(text(), 'Done')]")
            if safe_click(driver, continue_button_selector[0], continue_button_selector[1], wait_time=5):
                print("    Video/Passive content 'Continue' button clicked.")
                return True
            else:
                print("    Could not find 'Continue' button after video. Assuming auto-proceed or end of passive content. Manual intervention may be needed.")
                return False 
        except TimeoutException:
            print("    No explicit Video/Passive content detected. Trying generic submission.")
            try:
                generic_submit_button_selector = (By.XPATH, "//*[contains(@class, 'lrn-button') or contains(text(), 'Submit') or contains(text(), 'Next') or contains(text(), 'Done')]")
                if safe_click(driver, generic_submit_button_selector[0], generic_submit_button_selector[1], wait_time=5):
                    print("    Clicked generic Learnosity 'Next/Submit/Done' button.")
                    return True
                else:
                    print("    No generic 'Next/Submit/Done' button found in Learnosity. Stuck on this activity. Manual intervention may be needed.")
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
        time.sleep(random.uniform(2, 4)) 
        
        try:
            module_next_button_selector = (By.XPATH, "//button[contains(@class, 'MuiIconButton-root') and .//*[name()='svg' and @data-icon='eva-arrow-ios-forward-outline']]")
            
            if not safe_click(driver, module_next_button_selector[0], module_next_button_selector[1]):
                print("No more module navigation 'Next' buttons found or button not clickable. Assumed all activities in module completed or process ended.")
                break 
            
            print(f"Clicked module navigation 'Next' button. (Activity {processed_activities_count + 1})")
            processed_activities_count += 1
            time.sleep(random.uniform(3, 5)) 

            if switch_to_learnosity_iframe(driver):
                if process_learnosity_activity(driver):
                    print("    Activity in iframe successfully processed.")
                else:
                    print("    Failed to process activity in iframe. Manual intervention may be needed.")
                
                driver.switch_to.default_content()
                print("    Switched back to main page after iframe processing.")
            else:
                print("    No Learnosity iframe detected for this activity. Assuming main page interaction or completion.")
                
            time.sleep(random.uniform(2, 3)) 

        except TimeoutException:
            print("No more module navigation 'Next' buttons found. Assumed all activities in module completed or process ended.")
            break 
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
        wait.until(EC.presence_of_element_located((By.XPATH, "//h6[contains(text(), 'My Assignments')] | //h3[contains(text(), 'Dashboard')]")))
        print("Landed on dashboard.")

        assignment_list_items_selector = (By.XPATH, "//div[contains(@class, 'MuiBox-root') and .//h6[contains(text(), 'My Assignments')]]/following-sibling::div[contains(@class, 'MuiStack-root')]//div[contains(@class, 'MuiBox-root')]")
        
        assignment_list_items = driver.find_elements(assignment_list_items_selector[0], assignment_list_items_selector[1])
        
        if not assignment_list_items:
            print("No assignments found on the dashboard or couldn't locate assignment elements.")
            return
            
        print(f"Found {len(assignment_list_items)} potential assignments.")

        for i, assignment_item in enumerate(assignment_list_items):
            try:
                assignment_title_element = assignment_item.find_element(By.XPATH, ".//h6")
                assignment_title = assignment_title_element.text if assignment_title_element else f"Unknown Assignment {i+1}"
                
                start_button_selector = (By.XPATH, ".//button[contains(@class, 'MuiButtonBase-root')]") 
                
                print(f"\nProcessing Dashboard Assignment: {assignment_title}")
                
                if not safe_click(driver, start_button_selector[0], start_button_selector[1]):
                    print(f"    Failed to click start button for assignment: '{assignment_title}'. Skipping.")
                    continue 
                
                print(f"    Clicked to open assignment: '{assignment_title}'")
                time.sleep(random.uniform(4, 6)) 

                process_module_activities(driver)
                
                print("    Returning to dashboard to check for next assignment...")
                driver.get(DASHBOARD_URL)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//h6[contains(text(), 'My Assignments')] | //h3[contains(text(), 'Dashboard')]")))
                time.sleep(2) 

            except NoSuchElementException:
                print(f"    Could not find title or start button for dashboard assignment item {i+1}. Skipping.")
            except Exception as e:
                print(f"    An error occurred while trying to open/process dashboard assignment {assignment_title}: {e}")
                try:
                    driver.get(DASHBOARD_URL)
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//h6[contains(text(), 'My Assignments')] | //h3[contains(text(), 'Dashboard')]")))
                except:
                    print("    Failed to return to dashboard after error. Exiting assignment processing.")
                    return 

    except TimeoutException:
        print("Dashboard page did not load or assignments section not found.")
    except Exception as e:
        print(f"An unexpected error occurred during dashboard assignment processing: {e}")

# --- Unified login_to_hats_ladders function ---
def login_to_hats_ladders(driver, auth_method):
    """
    Handles login based on the specified authentication method.
    """
    print(f"Navigating to login page: {LOGIN_URL}")
    driver.get(LOGIN_URL)
    
    # Wait for potential overlays to disappear or for the page to stabilize
    wait = WebDriverWait(driver, 30) 

    # --- Wait for absence of common loading indicators/overlays (Customize these selectors!) ---
    loading_indicator_selector = (By.XPATH, "//*[contains(@class, 'loading-spinner') or contains(@class, 'modal-overlay') or contains(@class, 'MuiBackdrop-root')]")
    try:
        print("    Waiting for potential loading indicators/overlays to disappear...")
        wait.until(EC.invisibility_of_element_located(loading_indicator_selector))
        print("    Loading indicators/overlays seem to have disappeared.")
    except TimeoutException:
        print("    Timeout waiting for loading indicators/overlays to disappear. Proceeding anyway.")
    except NoSuchElementException:
        print("    No common loading indicators/overlays found.")

    time.sleep(5) # A short, fixed sleep can help with final rendering before clicking

    # --- Now attempt to click the login button ---
    if auth_method == "nyc_id":
        print(f"Attempting login with NYC.ID ({NYC_ID_USERNAME})...")
        if not NYC_ID_USERNAME or not NYC_ID_PASSWORD:
            raise ValueError("NYC.ID credentials (NYC_ID_USERNAME, NYC_ID_PASSWORD) not set in .env")

        # 1. Click 'Continue with NYC.ID' button on Hats & Ladders
        # This is the most accurate selector given your HTML snippet.
        nyc_id_signin_button_selector = (By.XPATH, "//a[span[text()='Continue with NYC.ID']]") 
        
        if not safe_click(driver, nyc_id_signin_button_selector[0], nyc_id_signin_button_selector[1]):
            raise Exception("Failed to click 'Continue with NYC.ID' button on Hats & Ladders login page after trying multiple selectors. Please inspect the element and any overlays.")

        print("Clicked 'Continue with NYC.ID'. Waiting for NYC.ID login page...")
        wait.until(EC.url_contains(NYC_ID_LOGIN_DOMAIN))
        print(f"Redirected to NYC.ID login page ({driver.current_url}).")

        # 2. Enter NYC.ID username/email
        # Selectors based on your provided HTML for NYC.ID login page (using precise IDs)
        nyc_id_username_input_selector = (By.ID, "gigya-loginID") 
        # Add a short wait specifically for the field to be visible and then try to send keys
        username_field_element = wait.until(EC.visibility_of_element_located(nyc_id_username_input_selector))
        username_field_element.clear() # Clear any pre-filled text
        driver.execute_script("arguments[0].focus();", username_field_element) # Explicitly focus
        username_field_element.send_keys(NYC_ID_USERNAME)
        print("    Entered NYC.ID username/email.")
        time.sleep(random.uniform(0.5, 1.0)) 

        # 3. Enter NYC.ID password
        nyc_id_password_input_selector = (By.ID, "gigya-password") 
        password_field_element = wait.until(EC.visibility_of_element_located(nyc_id_password_input_selector))
        password_field_element.clear() # Clear any pre-filled text
        driver.execute_script("arguments[0].focus();", password_field_element) # Explicitly focus
        password_field_element.send_keys(NYC_ID_PASSWORD)
        print("    Entered NYC.ID password.")
        time.sleep(random.uniform(0.5, 1.5)) 

        # 4. Click the NYC.ID login/submit button (using precise type and value from HTML)
        nyc_id_login_button_selector = (By.XPATH, "//input[@type='submit' and @value='Login']") 
        if not safe_click(driver, nyc_id_login_button_selector[0], nyc_id_login_button_selector[1]):
            raise Exception("Failed to click NYC.ID login button. Please check selector.")

        print("Clicked NYC.ID login button. Waiting for redirect back to Hats & Ladders...")
        wait.until(EC.url_contains(DASHBOARD_URL))
        print("Successfully redirected back to Hats & Ladders dashboard.")

    elif auth_method == "direct":
        print(f"Attempting direct login ({DIRECT_EMAIL})...")
        if not DIRECT_EMAIL or not DIRECT_PASSWORD:
            raise ValueError("Direct login credentials (DIRECT_EMAIL, DIRECT_PASSWORD) not set in .env")

        # Hats & Ladders direct login elements (from your screenshot for Hats & Ladders login page)
        # Username field (using placeholder text)
        username_field_selector = (By.XPATH, "//input[@placeholder='Enter username']")
        if not safe_send_keys(driver, username_field_selector[0], username_field_selector[1], DIRECT_EMAIL):
            raise Exception("Failed to enter direct email.")
        
        # Password field (using placeholder text)
        password_field_selector = (By.XPATH, "//input[@placeholder='Enter password']")
        if not safe_send_keys(driver, password_field_selector[0], password_field_selector[1], DIRECT_PASSWORD):
            raise Exception("Failed to enter direct password.")
        
        # 'Sign in' button for direct login (using button text)
        login_button_selector = (By.XPATH, "//button[text()='Sign in']") 
        if not safe_click(driver, login_button_selector[0], login_button_selector[1]):
             raise Exception("Failed to find or click direct login 'Sign in' button. Please check selector or any overlays.")
        
        print("Direct login attempt complete. Waiting for dashboard...")
        wait.until(EC.url_contains(DASHBOARD_URL)) 
        print("Successfully logged in via direct credentials.")

    else:
        raise ValueError(f"Unsupported authentication method: {auth_method}. Check AUTH_METHOD in .env. Must be 'nyc_id' or 'direct'.")
    
    # Final check for dashboard loading
    wait.until(EC.presence_of_element_located((By.XPATH, "//h6[contains(text(), '405 XP')]"))) # Or any other unique dashboard element
    print("Hats & Ladders dashboard fully loaded and confirmed.")
    return True


# --- Main Execution Flow ---
if __name__ == "__main__":
    driver = None
    try:
        if not LOGIN_URL:
            raise ValueError("LOGIN_URL is not set in your .env file.")

        driver = webdriver.Chrome(options=options)
        print("Browser started.")

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