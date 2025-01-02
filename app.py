from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import os
from datetime import datetime, timedelta
import random
import numpy as np
from gensim.models import KeyedVectors

app = Flask(__name__)
CORS(app)

# Load word embeddings model
model = KeyedVectors.load('glove-wiki-gigaword-50.model')
word_vectors = model.vectors

# Game state
target_word = None
daily_number = None
last_reset_date = None

def initialize_daily_word():
    global target_word, daily_number, last_reset_date
    current_date = datetime.now().date()
    
    if last_reset_date != current_date:
        # Get a random word from the model's vocabulary
        all_words = list(model.key_to_index.keys())
        valid_words = [w for w in all_words if w.isalpha() and len(w) >= 4]
        target_word = random.choice(valid_words)
        print(f"New target word: {target_word}")
        last_reset_date = current_date
        daily_number = (current_date - datetime(2024, 1, 1).date()).days

def calculate_similarity(word1, word2):
    try:
        return float(model.similarity(word1, word2))
    except KeyError:
        return None

@app.route('/')
def serve_index():
    return render_template('index.html')

@app.route('/api/guess', methods=['POST'])
def make_guess():
    initialize_daily_word()
    
    data = request.get_json()
    guess = data.get('word', '').lower()
    
    if not guess:
        return jsonify({'error': 'No word provided'}), 400
        
    try:
        similarity = calculate_similarity(guess, target_word)
        if similarity is None:
            return jsonify({'error': 'Word not in dictionary'}), 400
            
        response = {
            'similarity': similarity,
            'isCorrect': guess == target_word,
            'dailyNumber': daily_number
        }
        
        if guess == target_word:
            response['message'] = 'Congratulations! You found the word!'
            
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/give-up', methods=['POST'])
def give_up():
    initialize_daily_word()
    return jsonify({
        'word': target_word,
        'dailyNumber': daily_number,
        'message': f'The word was: {target_word}'
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    initialize_daily_word()
    return jsonify({
        'dailyNumber': daily_number,
        'totalPlayers': random.randint(1000, 5000)  # Simulated stat
    })

if __name__ == '__main__':
    app.run(debug=True)
