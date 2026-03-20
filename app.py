import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Import the analysis function from our analyzer module
from analyzer import analyze_text

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
        return jsonify({"error": "Missing 'text' key in JSON body."}), 400
        
    text_to_analyze = data['text']
    
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(port=port)
