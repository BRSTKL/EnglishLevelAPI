import os
# We use the dotenv library to load our secret API keys from the .env file.
from dotenv import load_dotenv

# We import the Google Generative AI library to interact with Gemini.
import google.generativeai as genai

# Load variables from the .env file into the system's environment variables.
load_dotenv()

# Get the GEMINI_API_KEY from the environment variables.
api_key = os.getenv("GEMINI_API_KEY")

# Configure the Gemini library with our API key so it's authorized to make requests.
genai.configure(api_key=api_key)

# We initialize the Gemini AI model we want to use.
# gemini-1.5-flash is extremely fast and part of the free tier.
# We also set some configuration options for the model:
# - temperature: 0.3 means the AI will be more focused, consistent, and less random.
# - max_output_tokens: 1000 limits the maximum length of the response to 1000 tokens (roughly 750 words).
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config={
        "temperature": 0.3,
        "max_output_tokens": 1000,
    }
)

def test_gemini_connection():
    """
    This is a simple function to test if our connection to Gemini is working.
    It sends a 'Hello' message and prints the response.
    """
    print("Testing connection to Google Gemini...")
    try:
        # We ask the model to generate content based on our prompt "Hello".
        response = model.generate_content("Hello")
        
        # If successful, we print out the text the AI responded with.
        print("Success! Gemini says: " + response.text)
    except Exception as e:
        # If there's an error (e.g., wrong API key placeholder), we print it out.
        print("\nAn error occurred. Make sure you replaced 'your_gemini_api_key_here' in the .env file!")
        print("Error details:", e)

# The code inside this block only runs if we run this script directly
# (e.g., by typing 'python ai_features.py' in the terminal).
if __name__ == "__main__":
    test_gemini_connection()
