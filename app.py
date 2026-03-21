import os
import re
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from functools import wraps

# Import the analysis function from our analyzer module
from analyzer import analyze_text

# Import our brand new AI simplification feature from ai_features.py
from ai_features import simplify_text

def validate_text(text, field_name="text"):
    """Validates the text input for length and content requirements."""
    if not text or not str(text).strip():
        return {"error": "Text cannot be empty", "code": 400}
        
    word_count = len(re.findall(r'\b\w+\b', str(text).lower()))
    
    if word_count < 10:
        return {"error": "Text too short. Send at least 10 words.", "code": 400}
    if word_count > 5000:
        return {"error": "Text too long. Maximum 5000 words allowed.", "code": 400}
        
    return None

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'changeme')

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[]
)

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Rate limit exceeded. Try again later.", "code": 429}), 429

def require_rapidapi_secret(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        expected_secret = os.environ.get('RAPIDAPI_SECRET')
        provided_secret = request.headers.get('X-RapidAPI-Proxy-Secret')
        
        if not expected_secret or not provided_secret or provided_secret != expected_secret:
            return jsonify({"error": "Unauthorized", "code": 401}), 401
            
        return f(*args, **kwargs)
    return decorated_function

@app.route('/analyze', methods=['POST'])
@limiter.limit("10 per minute")
@require_rapidapi_secret
def analyze_endpoint():
    """
    Endpoint that accepts JSON payload with 'text' and returns an analysis including a learning tip.
    """
    # 1. Check if the request contains valid JSON data
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({"error": "Missing field: text", "code": 400}), 400
        
    text_to_analyze = data['text']
    
    validation_error = validate_text(text_to_analyze, "text")
    if validation_error:
        return jsonify(validation_error), 400
    
    # 2. Get the analysis dictionary from the analyzer
    analysis_result = analyze_text(text_to_analyze)
    
    cefr_level = analysis_result['cefr_level']
    learning_tip = ""
    
    # 3. Create a learning tip based on the CEFR level
    if "A1" in cefr_level or "A2" in cefr_level:
        learning_tip = "Great for beginners! Simple and clear."
    elif "B1" in cefr_level or "B2" in cefr_level:
        learning_tip = "Suitable for intermediate learners."
    elif "C1" in cefr_level or "C2" in cefr_level:
        learning_tip = "Advanced content. Challenging vocabulary."
        
    # 4. Return the formatted JSON response mapping analyzer keys to the requested format
    response = {
        "cefr_level": cefr_level,
        "grade_level": analysis_result['grade_level'],
        "readability_score": analysis_result['reading_ease'],
        "word_count": analysis_result['total_words'],
        "sentence_count": analysis_result['total_sentences'],
        "unique_words": analysis_result['unique_words'],
        "complex_words": analysis_result['complex_words'],
        "learning_tip": learning_tip
    }
    
    return jsonify(response), 200

@app.route('/compare', methods=['POST'])
@limiter.limit("5 per minute")
@require_rapidapi_secret
def compare_endpoint():
    """
    Endpoint that accepts JSON payload with 'text1' and 'text2'
    and returns a comparison of both texts' difficulty and CEFR levels.
    """
    # 1. Grab JSON data from the request
    data = request.get_json()
    
    if not data or 'text1' not in data:
        return jsonify({"error": "Missing field: text1", "code": 400}), 400
    if 'text2' not in data:
        return jsonify({"error": "Missing field: text2", "code": 400}), 400
        
    text1 = data['text1']
    text2 = data['text2']
    
    val_err1 = validate_text(text1, "text1")
    if val_err1:
        return jsonify(val_err1), 400
        
    val_err2 = validate_text(text2, "text2")
    if val_err2:
        return jsonify(val_err2), 400
    
    # 2. Analyze both texts using our unified logic
    analysis1 = analyze_text(text1)
    analysis2 = analyze_text(text2)
    
    # 3. Create a helper mapping for CEFR levels to calculate distance
    cefr_map = {
        "A1 (Beginner)": 1,
        "A2 (Elementary)": 2,
        "B1 (Intermediate)": 3,
        "B2 (Upper-Intermediate)": 4,
        "C1 (Advanced)": 5,
        "C2 (Mastery)": 6
    }
    
    cefr1 = analysis1['cefr_level']
    cefr2 = analysis2['cefr_level']
    
    level1_val = cefr_map.get(cefr1, 1)
    level2_val = cefr_map.get(cefr2, 1)
    
    diff = abs(level1_val - level2_val)
    
    # 4. Determine which text is harder and write a recommendation
    if level1_val > level2_val:
        harder = "text1"
        rec = "text1 is significantly more advanced than text2" if diff > 1 else "text1 is slightly more advanced than text2"
    elif level2_val > level1_val:
        harder = "text2"
        rec = "text2 is significantly more advanced than text1" if diff > 1 else "text2 is slightly more advanced than text1"
    else:
        # Fall back to checking grade level if CEFR is exactly the same
        if analysis1['grade_level'] > analysis2['grade_level']:
            harder = "text1"
            rec = "text1 has a slightly higher reading grade than text2 despite being the same CEFR level"
        elif analysis2['grade_level'] > analysis1['grade_level']:
            harder = "text2"
            rec = "text2 has a slightly higher reading grade than text1 despite being the same CEFR level"
        else:
            harder = "equal"
            rec = "Both texts are at approximately the same difficulty"
            
    # Format the level difference using the required language
    if diff == 0:
        level_difference = "0 CEFR levels apart"
    elif diff == 1:
        level_difference = "1 CEFR level apart"
    else:
        level_difference = f"{diff} CEFR levels apart"
        
    # 5. Build the final response match layout requested by user
    response = {
        "text1": {
            "cefr_level": cefr1,
            "grade_level": analysis1['grade_level'],
            "word_count": analysis1['total_words']
        },
        "text2": {
            "cefr_level": cefr2,
            "grade_level": analysis2['grade_level'],
            "word_count": analysis2['total_words']
        },
        "comparison": {
            "harder_text": harder,
            "level_difference": level_difference,
            "recommendation": rec
        }
    }
    
    return jsonify(response), 200

@app.route('/simplify', methods=['POST'])
@limiter.limit("5 per minute")  # We restrict users to 5 requests per minute so they don't abuse the AI
@require_rapidapi_secret        # This protects our endpoint from unauthorized users
def simplify_endpoint():
    """
    Endpoint that simplifies text using Gemini to a specific English level.
    """
    # 1. Grab carefully the JSON data sent to us by the user
    data = request.get_json()
    
    # 2. Add error handling: check if the 'text' field is entirely missing
    if not data or 'text' not in data:
        # We inform the user they missed a required field with a 400 Bad Request error.
        return jsonify({"error": "Missing field: text", "code": 400}), 400
        
    text = data['text']
    
    # 3. Add error handling: Add 'target_level' field check
    # We use data.get() to grab it without giving an error if it doesn't exist
    target_level = data.get('target_level')
    
    # 4. Add error handling: Check if target_level is allowed
    # The user is only allowed to send these exact strings
    valid_levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
    if target_level not in valid_levels:
        # If it's invalid (e.g., "Z9" or missing), we block it with a 400 error.
        return jsonify({"error": f"Invalid target_level. Must be one of: {', '.join(valid_levels)}", "code": 400}), 400
        
    # 5. Let's make sure the text isn't weird (empty or millions of words) using our trusty old validator
    val_err = validate_text(text, "text")
    if val_err:
        return jsonify(val_err), 400
        
    # 6. To tell them what level it used to be, we analyze their original text in the background!
    analysis = analyze_text(text)
    
    # The analyzer natively returns labels like "C1 (Advanced)".
    # But we ONLY want the "C1" part to keep our API clean exactly how we described!
    # By splitting at the empty space (" "), we take just the very first part: [0]
    original_cefr_label = analysis['cefr_level']
    original_cefr = original_cefr_label.split(" ")[0]
    
    # 7. Add error handling for Gemini!
    # We use a try/except block. Connecting to an outside API (Google) is risky and could fail.
    try:
        # We hand off the text to our neat function inside ai_features.py
        simplified_text = simplify_text(text, target_level)
    except Exception as e:
        # If Gemini fails (API quota run out, network offline, etc.), we catch it here.
        print("Gemini API Error:", e)
        # We respond with a 503 Service Unavailable error instead of crashing our server!
        return jsonify({"error": "AI service unavailable", "code": 503}), 503
        
    # 8. Create the exact dictionary structure you expected as an answer
    response_data = {
        "original_text": text,
        "simplified_text": simplified_text,
        "target_level": target_level,
        "original_cefr": original_cefr
    }
    
    # 9. Send the beautiful JSON data back to the person who requested it! (200 OK means Success)
    return jsonify(response_data), 200

@app.route('/health', methods=['GET'])
def health_endpoint():
    """Health check endpoint to verify the API is running."""
    return jsonify({"status": "ok", "version": "1.0.0"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
