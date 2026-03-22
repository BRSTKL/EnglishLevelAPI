import os
# The dotenv library lets us securely load secret API keys from the .env file.
from dotenv import load_dotenv

# We import the new, officially supported Google GenAI library. 
from google import genai

# We call this to actually load those variables from .env into our system environment.
load_dotenv()


def test_gemini_connection():
    """
    This is a function specifically meant to test if we successfully log into Gemini.
    It attempts to send a 'Hello' message and awaits the AI's response.
    """
    print("Testing connection to Google Gemini...")
    
    # Initialize the client specifically when this function runs!
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    # We use a try/except block. If something crashes (like an invalid API key), 
    # the code gracefully jumps down to 'except' instead of breaking our app entirely.
    try:
        # We ask the client to generate content using the gemini-2.5-flash model,
        # which is the newest and fastest version available.
        # We give it a simple instruction: "Hello"
        # Since you wanted consistent responses (temperature 0.3) and max 1000 tokens,
        # we configure that directly in the generate_content call.
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents="Hello",
            config={
                "temperature": 0.3,
                "max_output_tokens": 1000,
            }
        )
        
        # If the above line succeeded, the AI's text response is printed out cleanly.
        print("Success! Gemini says: " + response.text)
    except Exception as e:
        # If there's an issue (e.g., forgetting to update 'your_gemini_api_key_here'), 
        # we print it nicely for the developer (you) to see.
        print("\nAn error occurred. Make sure you replaced 'your_gemini_api_key_here' in the .env file!")
        print("Error details:", e)

def simplify_text(text, target_level):
    """
    Sends a request to Gemini to rewrite the text to a specific CEFR level.
    """
    # Initialize the client exactly when this function runs!
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    # 1. We prepare exactly what we want to say to the AI.
    # The 'f' inside the quotation marks lets us inject our variables '{target_level}' and '{text}' directly into the string.
    prompt = f"""Rewrite the following text at {target_level} English level. Use simple words and short sentences.
Keep the same meaning. Return ONLY the rewritten text, nothing else.

Text: {text}"""
    
    # 2. We ask our Gemini client to generate the content based on our prompt.
    response = client.models.generate_content(
        # We use the fast and smart 2.5 model
        model="gemini-2.5-flash",
        # We give it our carefully written instructions
        contents=prompt,
        config={
            # We keep the temperature low so we get consistent, straightforward text instead of crazy/creative variations.
            "temperature": 0.3,
            "max_output_tokens": 1000,
        }
    )
    
    # 3. The AI returns a bunch of data, but we only care about the actual text string it generated.
    # .strip() removes any accidental empty spaces or newlines at the beginning or end of the text.
    return response.text.strip()

# This simply means: only run "test_gemini_connection" if we're directly running THIS specific Python file.
# That way, when we import this file later in app.py or analyzer.py to actually build features, 
# it doesn't randomly run a test every time.
if __name__ == "__main__":
    test_gemini_connection()
