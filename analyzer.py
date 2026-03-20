import textstat
import re

def get_cefr_level(grade_level: float) -> str:
    """Helper function to map the grade level to a CEFR level."""
    # Round the grade level to the nearest whole number to make checking easier
    grade = round(grade_level)
    
    # Map the grade to the corresponding CEFR level based on the rules
    if grade <= 2:
        return "A1 (Beginner)"
    elif 3 <= grade <= 4:
        return "A2 (Elementary)"
    elif 5 <= grade <= 6:
        return "B1 (Intermediate)"
    elif 7 <= grade <= 9:
        return "B2 (Upper-Intermediate)"
    elif 10 <= grade <= 12:
        return "C1 (Advanced)"
    else:
        return "C2 (Mastery)"

def analyze_text(text: str) -> dict:
    """
    Analyzes the provided text and returns readability statistics and word counts.
    """
    # 1. Calculate reading ease and grade level using textstat
    reading_ease = textstat.flesch_reading_ease(text)
    grade_level = textstat.flesch_kincaid_grade(text)
    
    # 2. Get the CEFR level from our helper function
    cefr_level = get_cefr_level(grade_level)
    
    # 3. Count total sentences, words, and unique words
    # Split text into words, removing punctuation to keep it clean
    words = re.findall(r'\b\w+\b', text.lower())
    
    total_words = len(words)
    total_sentences = textstat.sentence_count(text)
    
    # If textstat sentence count is 0 but there are words, assume 1 sentence at least
    if total_sentences == 0 and total_words > 0:
        total_sentences = 1
        
    unique_words_count = len(set(words))
    
    # 4. Find complex words (longer than 8 characters)
    # We use a set first to avoid duplicated complex words
    complex_words_set = {word for word in words if len(word) > 8}
    
    # Take the first 10 complex words as a list
    complex_words_list = list(complex_words_set)[:10]
    
    # 5. Return everything as a Python dictionary
    return {
        "reading_ease": reading_ease,
        "grade_level": grade_level,
        "cefr_level": cefr_level,
        "total_words": total_words,
        "total_sentences": total_sentences,
        "unique_words": unique_words_count,
        "complex_words": complex_words_list
    }
