from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import time
import random # For simulating human-like delays or varied responses

# --- Configuration ---
# Your Hats & Ladders credentials
USERNAME = "your-email@example.com"
PASSWORD = "yourpassword"

# URLs for Hats & Ladders
login_url = "https://hatsandladders.com/login"
dashboard_url = "https://hatsandladders.com/climber/dashboard" # Your main dashboard URL
# You can uncomment this and use it if you want to test a specific climb directly
# career_climb_test_url = "https://hatsandladders.com/career-climbs/example-career-climb-id" 

# Browser options (run headless for background execution, remove for visual debugging)
options = webdriver.ChromeOptions()
# options.add_argument("--headless")  # Uncomment to run without a visible browser window
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

def switch_to_learnosity_iframe(driver, wait_time=20):
    """Waits for and switches to the Learnosity iframe."""
    try:
        # Prioritize finding by ID if known, otherwise by src.
        # Inspect your live page to find the most stable way to locate this iframe.
        # A common Learnosity iframe won't have the 'x-origin-frame' class.
        iframe_selector = (By.XPATH, "//iframe[contains(@src, 'learnosity.com') and not(contains(@class, 'x-origin-frame'))]")
        
        WebDriverWait(driver, wait_time).until(
            EC.frame_to_be_available_and_switch_to_it(iframe_selector)
        )
        print("    Switched to Learnosity iframe.")
        return True
    except TimeoutException:
        print("    Timeout: Learnosity iframe not found or not available.")
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
        
        # Scenario 1: Quiz (Multiple Choice/Radio Button)
        try:
            # Look for a common quiz question element (e.g., a specific Learnosity question container class)
            quiz_question_container = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'lrn-question') or contains(@class, 'lrn-multiplechoice')]"))
            )
            print("    Detected Quiz activity.")
            
            # Find all possible answer options (e.g., radio buttons or checkboxes)
            # This is a very generic XPath; adapt based on actual HTML
            answer_options = quiz_question_container.find_elements(By.XPATH, ".//input[@type='radio' or @type='checkbox']/ancestor::label")
            
            if answer_options:
                # --- QUIZ ANSWER LOGIC ---
                # This is where your "cheat" logic would go.
                # 1. Scrape the question: quiz_question_container.find_element(By.CLASS_NAME, "lrn-question-label").text
                # 2. Scrape options: [opt.text for opt in answer_options]
                # 3. Look up correct answer from a list/dictionary, or use an LLM API.
                # For now, let's just pick a random answer or the first one.
                
                # Example: Always pick the first option
                selected_option = answer_options[0] 
                # Example: Pick a random option
                # selected_option = random.choice(answer_options)

                print(f"    Selecting answer: {selected_option.text if selected_option.text else ' (no visible text)'}")
                selected_option.click() # Click the label or the input directly

                time.sleep(random.uniform(1, 2)) # Simulate reading/thinking time
                
                # Find and click the Learnosity submit/next button (often within a specific class)
                # These buttons typically have specific Learnosity classes like 'lrn-response-button'
                submit_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//*[contains(@class, 'lrn-button') or contains(@class, 'lrn-save-button') or contains(text(), 'Submit') or contains(text(), 'Next')]"))
                )
                submit_button.click()
                print("    Quiz answer submitted.")
                return True
            else:
                print("    No answer options found for quiz.")
                return False

        except TimeoutException:
            # Not a quiz, try other types
            pass
        
        # Scenario 2: Reflection Prompt (Text Area)
        try:
            reflection_textarea = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, "//textarea[contains(@class, 'lrn-text-input') or @aria-label='Reflection response']"))
            )
            print("    Detected Reflection activity.")
            
            # Pre-defined response or generate one
            reflection_text = "This is an automated response to the reflection prompt. I found the content insightful and will apply these learnings to my career path."
            reflection_textarea.send_keys(reflection_text)
            print("    Reflection text entered.")
            
            time.sleep(random.uniform(1, 2)) # Simulate typing time
            
            # Find and click the Learnosity submit button
            submit_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(@class, 'lrn-button') or contains(text(), 'Submit')]"))
            )
            submit_button.click()
            print("    Reflection submitted.")
            return True
        except TimeoutException:
            # Not a reflection, try other types
            pass
            
        # Scenario 3: Video or Passive Content (Just wait for it to finish or for a 'continue' button)
        try:
            video_player = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'lrn-video-player') or contains(@class, 'lrn-activity-video')]"))
            )
            print("    Detected Video/Passive content. Waiting for duration...")
            # Estimate video duration or look for a 'skip' button if available.
            # For simplicity, wait a fixed time.
            time.sleep(random.uniform(8, 15)) # Simulate watching video
            
            # After video, look for a "Continue" or "Next" button within the iframe
            continue_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(@class, 'lrn-button') or contains(text(), 'Continue') or contains(text(), 'Next')]"))
            )
            continue_button.click()
            print("    Video/Passive content 'Continue' button clicked.")
            return True
        except TimeoutException:
            print("    No specific Learnosity activity type detected (quiz, reflection, video). Assuming passive content or unknown type. Attempting generic 'Next/Submit'...")
            try:
                 # Last resort: Try to find a generic next/submit button in Learnosity
                generic_submit_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//*[contains(@class, 'lrn-button') or contains(text(), 'Submit') or contains(text(), 'Next') or contains(text(), 'Done')]"))
                )
                generic_submit_button.click()
                print("    Clicked generic Learnosity 'Next/Submit' button.")
                return True
            except TimeoutException:
                print("    No generic 'Next/Submit' button found in Learnosity. Stuck on this activity.")
                return False

    except Exception as e:
        print(f"    An error occurred during Learnosity activity processing: {e}")
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
            # This is the button that moves to the next activity tile or overall module completion.
            # Based on your HTML, it's often a right-arrow icon button in the main page content.
            # The XPath targets a button with a right arrow icon (eva-arrow-ios-forward-outline).
            # This is a general 'next' button for moving between activity tiles on the main page.
            module_next_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'MuiIconButton-root') and .//*[name()='svg' and @data-icon='eva-arrow-ios-forward-outline']]"))
            )
            
            module_next_button.click()
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
                print("    No Learnosity iframe detected for this activity, assuming main page interaction or completion.")
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
    driver.get(dashboard_url)
    wait = WebDriverWait(driver, 15)
    
    try:
        # Wait for a known element on the dashboard indicating it's loaded
        wait.until(EC.presence_of_element_located((By.XPATH, "//h6[contains(text(), 'My Assignments')] | //h3[contains(text(), 'Dashboard')]")))
        print("Landed on dashboard.")

        # --- IMPORTANT: Customize these selectors for your dashboard's assignment list ---
        # Look for elements that represent individual assignments.
        # Example: Find all div elements with a specific class that wraps each assignment
        # You'll need to inspect your live dashboard HTML for these selectors!
        assignment_list_items = driver.find_elements(By.XPATH, "//div[contains(@class, 'MuiBox-root') and .//h6[contains(text(), 'My Assignments')]]/following-sibling::div[contains(@class, 'MuiStack-root')]//div[contains(@class, 'MuiBox-root')]")
        
        if not assignment_list_items:
            print("No assignments found on the dashboard or couldn't locate assignment elements.")
            return
            
        print(f"Found {len(assignment_list_items)} potential assignments.")

        for i, assignment_item in enumerate(assignment_list_items):
            try:
                # Find the title of the assignment
                assignment_title_element = assignment_item.find_element(By.XPATH, ".//h6")
                assignment_title = assignment_title_element.text if assignment_title_element else f"Unknown Assignment {i+1}"
                
                # Find the link or button to start/continue this specific assignment
                # This could be an <a> tag, or a <button> with a right arrow icon.
                # Inspect your dashboard for the correct selector.
                start_button = assignment_item.find_element(By.XPATH, ".//button[contains(@class, 'MuiButtonBase-root')]") # Or a more specific XPath for the 'start' button
                
                print(f"\nProcessing Dashboard Assignment: {assignment_title}")
                
                # Click the assignment to navigate to its module page
                start_button.click()
                print(f"    Clicked to open assignment: '{assignment_title}'")
                time.sleep(random.uniform(4, 6)) # Wait for the assignment page to load

                # Once on the assignment's module page, use the existing module processing logic
                process_module_activities(driver)
                
                # After completing a module, the page might return to the dashboard
                # or stay on a completion screen. You might need to explicitly go back
                # to the dashboard to find the next assignment.
                print("    Returning to dashboard to check for next assignment...")
                driver.get(dashboard_url)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//h6[contains(text(), 'My Assignments')] | //h3[contains(text(), 'Dashboard')]")))
                time.sleep(2) # Give it a moment to refresh the assignment list

            except NoSuchElementException:
                print(f"    Could not find title or start button for assignment item {i+1}. Skipping.")
            except Exception as e:
                print(f"    An error occurred while trying to open/process assignment {assignment_title}: {e}")
                # Try to navigate back to dashboard to continue with other assignments
                try:
                    driver.get(dashboard_url)
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//h6[contains(text(), 'My Assignments')] | //h3[contains(text(), 'Dashboard')]")))
                except:
                    print("    Failed to return to dashboard after error. Exiting assignment processing.")
                    return # Exit if we can't get back to dashboard

    except TimeoutException:
        print("Dashboard page did not load or assignments section not found.")
    except Exception as e:
        print(f"An unexpected error occurred during dashboard assignment processing: {e}")


# --- Main Execution Flow ---
if __name__ == "__main__":
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        print("Browser started.")

        # 1. Login
        print("Navigating to login page...")
        driver.get(login_url)

        wait = WebDriverWait(driver, 20)

        username_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        
        username_field.send_keys(USERNAME)
        password_field.send_keys(PASSWORD)
        
        # Look for a login button that has 'Login' text within its span
        login_button_selector = "//button[span[text()='Login']]"
        if not safe_click(driver, By.XPATH, login_button_selector):
             # Fallback if the above XPath doesn't work (e.g., button text is not direct span)
             login_button_selector = "//button[contains(text(), 'Login')]" # Try with contains
             if not safe_click(driver, By.XPATH, login_button_selector):
                 # Last resort: find by a common MUI button class or form submit
                 login_button_selector = "//form//button[@type='submit']"
                 if not safe_click(driver, By.XPATH, login_button_selector):
                    raise Exception("Failed to find or click login button.")

        print("Login attempt complete. Waiting for dashboard...")
        
        # Wait for a characteristic element on the dashboard to confirm login
        wait.until(EC.url_contains("/climber/dashboard") or EC.presence_of_element_located((By.XPATH, "//h6[contains(text(), '405 XP')]"))) # Your XP display

        print("Successfully logged in.")

        # --- Choose your automation path ---
        
        # OPTION 1: Process assignments from the dashboard
        process_dashboard_assignments(driver)

        # OPTION 2: Directly go to a specific career climb (uncomment if you prefer this)
        # print(f"\n--- Directly navigating to specific career climb: {career_climb_test_url} ---")
        # driver.get(career_climb_test_url)
        # process_module_activities(driver)


    except Exception as e:
        print(f"\nAn unrecoverable error occurred: {e}")
        # Optionally, save a screenshot for debugging
        if driver:
            driver.save_screenshot("error_screenshot.png")
            print("Screenshot saved as error_screenshot.png")

    finally:
        if driver:
            print("\nClosing browser...")
            driver.quit()
        print("Program finished.")