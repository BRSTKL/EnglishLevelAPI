import os
import re
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Import the analysis function from our analyzer module
from analyzer import analyze_text

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
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'changeme')

@app.route('/analyze', methods=['POST'])
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

@app.route('/health', methods=['GET'])
def health_endpoint():
    """Health check endpoint to verify the API is running."""
    return jsonify({"status": "ok", "version": "1.0.0"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(port=port)
