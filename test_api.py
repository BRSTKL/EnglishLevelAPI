import subprocess
import time
import requests
import sys
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:5000"
SECRET = os.environ.get("RAPIDAPI_SECRET", "my_super_secret_rapidapi_key")
HEADERS = {"X-RapidAPI-Proxy-Secret": SECRET}
HEADERS_NO_AUTH = {}

def print_result(test_num, name, passed, detail=""):
    if passed:
        print(f"✅ Test {test_num} PASSED - {name}")
    else:
        print(f"❌ Test {test_num} FAILED - {name}")
        if detail:
            print(f"   Detail: {detail}")

def run_tests():
    print("Starting Flask server...")
    # Start the server in the background
    server_process = subprocess.Popen([sys.executable, "app.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Wait until server is up
    for _ in range(10):
        try:
            requests.get(f"{BASE_URL}/health")
            break
        except requests.exceptions.ConnectionError:
            time.sleep(1)

    try:
        # Test 1 - /health
        try:
            r1 = requests.get(f"{BASE_URL}/health")
            passed = r1.status_code == 200 and r1.json().get("status") == "ok"
            detail = "" if passed else f"Expected 200/ok, got {r1.status_code}/{r1.text}"
            print_result(1, "/health returned ok", passed, detail)
        except Exception as e:
            print_result(1, "/health returned ok", False, str(e))

        # Test 2 - /analyze with valid text (50+ words)
        valid_text = (
            "This is a substantially long paragraph designed to test the analyzer functionality. "
            "It contains enough words to comfortably surpass the ten word minimum requirement set by the API. "
            "We are using this text to verify that the Flesch Reading Ease and Flesch Kincaid Grade Level calculations "
            "are working properly. The CEFR level should be calculated and returned within a structured JSON format along "
            "with word and sentence counts, completing the requirement for a valid text analysis execution."
        )
        try:
            r2 = requests.post(f"{BASE_URL}/analyze", json={"text": valid_text}, headers=HEADERS)
            passed = r2.status_code == 200 and "cefr_level" in r2.json()
            detail = "" if passed else f"Expected 200/cefr_level, got {r2.status_code}/{r2.text}"
            print_result(2, "/analyze valid text returned CEFR level", passed, detail)
        except Exception as e:
            print_result(2, "/analyze valid text returned CEFR level", False, str(e))

        # Test 3 - /analyze with empty text
        try:
            r3 = requests.post(f"{BASE_URL}/analyze", json={"text": "   "}, headers=HEADERS)
            passed = r3.status_code == 400 and r3.json().get("code") == 400
            detail = "" if passed else f"Expected 400, got {r3.status_code}/{r3.text}"
            print_result(3, "/analyze with empty text returned 400", passed, detail)
        except Exception as e:
            print_result(3, "/analyze with empty text returned 400", False, str(e))

        # Test 4 - /analyze with no "text" field
        try:
            r4 = requests.post(f"{BASE_URL}/analyze", json={"wrong_field": "hello"}, headers=HEADERS)
            passed = r4.status_code == 400
            detail = "" if passed else f"Expected 400, got {r4.status_code}/{r4.text}"
            print_result(4, "/analyze with no 'text' field returned 400", passed, detail)
        except Exception as e:
            print_result(4, "/analyze with no 'text' field returned 400", False, str(e))

        # Test 5 - /analyze with text under 10 words
        try:
            r5 = requests.post(f"{BASE_URL}/analyze", json={"text": "Too short text."}, headers=HEADERS)
            passed = r5.status_code == 400
            detail = "" if passed else f"Expected 400, got {r5.status_code}/{r5.text}"
            print_result(5, "/analyze with text under 10 words returned 400", passed, detail)
        except Exception as e:
            print_result(5, "/analyze with text under 10 words returned 400", False, str(e))

        # Test 6 - /compare with two different texts
        text1 = "This text is very simple and short. I am testing it right now to see what happens."
        text2 = "Furthermore, this subsequent document exemplifies a substantially higher degree of lexical sophistication and syntactical complexity, establishing unequivocally its advanced difficulty paradigm."
        try:
            r6 = requests.post(f"{BASE_URL}/compare", json={"text1": text1, "text2": text2}, headers=HEADERS)
            passed = r6.status_code == 200 and "comparison" in r6.json()
            detail = "" if passed else f"Expected 200/comparison, got {r6.status_code}/{r6.text}"
            print_result(6, "/compare with two texts returned comparison", passed, detail)
        except Exception as e:
            print_result(6, "/compare with two texts returned comparison", False, str(e))

        # Test 7 - /analyze without RapidAPI secret header
        try:
            r7 = requests.post(f"{BASE_URL}/analyze", json={"text": valid_text}, headers=HEADERS_NO_AUTH)
            passed = r7.status_code == 401
            detail = "" if passed else f"Expected 401, got {r7.status_code}/{r7.text}"
            print_result(7, "/analyze without RapidAPI header returned 401", passed, detail)
        except Exception as e:
            print_result(7, "/analyze without RapidAPI header returned 401", False, str(e))

    finally:
        print("Shutting down Flask server...")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    run_tests()
