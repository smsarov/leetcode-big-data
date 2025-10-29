import requests
import csv
import json
import time

# --- Configuration ---
BASE_URL = "http://localhost:3000"
INPUT_FILE = "users.csv"
LANGUAGE_STATS_OUTPUT = "language_stats.csv"
SOLVED_STATS_OUTPUT = "solved_stats.csv"
MAX_RETRIES = 3
INITIAL_BACKOFF = 0.1  # seconds

START_INDEX = 29000      # Starting index (0-based) in users.csv
PROCESS_COUNT = 84540 # Number of users to process starting from START_INDEX
THROTTLE_DELAY_SEC = 0.1 # Delay between processing each user to prevent rate limiting
INITIAL_START_DELAY_SEC = 0 # Delay the start of the entire script by 1 hour (3600 seconds)

# --- Helper Functions for API and Robustness ---

def fetch_data_with_retry(url):
    """Fetches data from a URL with exponential backoff for robustness."""
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            # Handle connection errors, timeouts, and HTTP errors
            print(f"Error fetching {url} for attempt {attempt + 1}: {e}")
            if attempt < MAX_RETRIES - 1:
                sleep_time = INITIAL_BACKOFF * (2 ** attempt)
                time.sleep(sleep_time)
                continue
            return None # Failed after all retries

# --- Feature Extraction Functions ---

def get_count_by_difficulty(data_array, difficulty_name):
    """Safely finds the 'count' value for a specific difficulty in the API arrays."""
    if not data_array:
        return 0
    for item in data_array:
        if item.get("difficulty") == difficulty_name:
            # We want the 'count' of problems (not 'submissions')
            return item.get("count", 0)
    return 0

def extract_solved_stats(username, solved_data):
    """
    Creates a single row record for the solved_stats table: 
    username, easy, medium, hard, ac_easy, ac_medium, ac_hard
    """
    default_record = {
        "username": username, "easy": 0, "medium": 0, "hard": 0,
        "ac_easy": 0, "ac_medium": 0, "ac_hard": 0
    }
    if not solved_data:
        return default_record

    total_submissions = solved_data.get("totalSubmissionNum", [])
    accepted_submissions = solved_data.get("acSubmissionNum", [])

    return {
        "username": username,
        # Total Solved Problems (All, Easy, Medium, Hard)
        "easy": get_count_by_difficulty(total_submissions, "Easy"),
        "medium": get_count_by_difficulty(total_submissions, "Medium"),
        "hard": get_count_by_difficulty(total_submissions, "Hard"),
        # Accepted Problems (Easy, Medium, Hard)
        "ac_easy": get_count_by_difficulty(accepted_submissions, "Easy"),
        "ac_medium": get_count_by_difficulty(accepted_submissions, "Medium"),
        "ac_hard": get_count_by_difficulty(accepted_submissions, "Hard")
    }

def extract_language_stats(username, lang_data):
    """
    Creates multiple row records for the language_stats table:
    username, languageName, problemsSolved
    """
    records = []
    if not lang_data:
        return records

    lang_counts = lang_data.get("matchedUser", {}).get("languageProblemCount", [])
    
    for item in lang_counts:
        records.append({
            "username": username,
            "languageName": item.get("languageName", "Unknown"),
            "problemsSolved": item.get("problemsSolved", 0)
        })
    
    return records


def process_user_data(username):
    """
    Fetches required data and returns structured records for both tables.
    Returns (language_records, solved_record)
    """
    
    # --- 1. Fetch Solved Data ---
    solved_url = f"{BASE_URL}/{username}/solved"
    solved_data = fetch_data_with_retry(solved_url)
    solved_record = extract_solved_stats(username, solved_data)

    # --- 2. Fetch Language Data ---
    lang_url = f"{BASE_URL}/languageStats?username={username}"
    lang_data = fetch_data_with_retry(lang_url)
    language_records = extract_language_stats(username, lang_data)

    return language_records, solved_record

# --- Main Logic ---

def main():
    """
    Main function to orchestrate the reading, processing, and STREAMING of data 
    into two separate CSV files, applying pagination.
    """
    # Apply initial delay
    if INITIAL_START_DELAY_SEC > 0:
        delay_hours = INITIAL_START_DELAY_SEC / 3600
        # Calculate when the script will start running
        start_time = time.time() + INITIAL_START_DELAY_SEC
        print(f"Delaying script execution by {delay_hours:.2f} hours ({INITIAL_START_DELAY_SEC} seconds).")
        print(f"The script is scheduled to start processing at approximately: {time.ctime(start_time)}")
        time.sleep(INITIAL_START_DELAY_SEC)
        print("Delay complete. Starting data processing.")
        
    try:
        with open(INPUT_FILE, mode='r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            usernames = [row['username'].strip() for row in reader]
    except FileNotFoundError:
        print(f"Error: Input file '{INPUT_FILE}' not found. Please create it.")
        return

    # --- Apply Pagination Logic ---
    total_users = len(usernames)
    
    if START_INDEX >= total_users:
        print(f"Error: START_INDEX ({START_INDEX}) is beyond the total number of users ({total_users}). Exiting.")
        return

    # Calculate the end index (exclusive)
    end_index = min(START_INDEX + PROCESS_COUNT, total_users)
    
    # Slice the list to get the users for the current batch
    usernames_to_process = usernames[START_INDEX:end_index]
    actual_count = len(usernames_to_process)

    print(f"Total users found: {total_users}")
    print(f"Applying pagination: Starting at index {START_INDEX} and processing {actual_count} user(s).")
    
    if actual_count == 0:
        print("No users to process based on START_INDEX and PROCESS_COUNT. Exiting.")
        return

    # --- Define Fieldnames ---
    lang_fieldnames = ["username", "languageName", "problemsSolved"]
    solved_fieldnames = [
        "username", "easy", "medium", "hard", 
        "ac_easy", "ac_medium", "ac_hard"
    ]
    
    processed_count = 0

    try:
        # Open both CSV files for writing (once)
        with open(LANGUAGE_STATS_OUTPUT, mode='a', newline='', encoding='utf-8') as lang_outfile, \
             open(SOLVED_STATS_OUTPUT, mode='a', newline='', encoding='utf-8') as solved_outfile:

            # Initialize DictWriters
            lang_writer = csv.DictWriter(lang_outfile, fieldnames=lang_fieldnames, extrasaction='ignore')
            solved_writer = csv.DictWriter(solved_outfile, fieldnames=solved_fieldnames, extrasaction='ignore')

            # Write headers for both files
            lang_writer.writeheader()
            solved_writer.writeheader()
            
            # Process each user sequentially
            for username in usernames_to_process:
                if username:
                    try: 
                        print(f"Processing data for user: {username}")
                        
                        lang_records, solved_record = process_user_data(username)
                        
                        # 1. Write to Language Stats Table (Multi-Row)
                        if lang_records:
                            lang_writer.writerows(lang_records)
                            
                        # 2. Write to Solved Stats Table (Single-Row)
                        if solved_record:
                            solved_writer.writerow(solved_record)

                        lang_outfile.flush()
                        solved_outfile.flush()
                            
                        processed_count += 1
                        print(f"--> Data written for {username}. Total processed: {processed_count}")
                        
                        # Throttle the process to prevent rate-limiting errors
                        time.sleep(THROTTLE_DELAY_SEC)
                    except Exception as e:
                        print(f"An error occurred while parsing {username}")


    except Exception as e:
        print("Script finished with unexpected reasons")

    print(f"\nProcessing finished. Successfully generated two tables with data for {processed_count} users.")
    print(f"- Language Stats Table: '{LANGUAGE_STATS_OUTPUT}'")
    print(f"- Solved Stats Table: '{SOLVED_STATS_OUTPUT}'")


if __name__ == "__main__":
    main()
