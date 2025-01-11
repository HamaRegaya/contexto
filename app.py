from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import os
from datetime import datetime, timedelta
import random
import numpy as np
from gensim.models import KeyedVectors
from langchain.schema import HumanMessage
from LLM import llm  # Import the existing LLM
from dotenv import load_dotenv
import gensim.downloader as api

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Load word embeddings model
print("Loading word embeddings model...")
model = KeyedVectors.load('glove-wiki-gigaword-300.model')
word_vectors = model.vectors
print("Model loaded!")

# Game state
class GameState:
    def __init__(self):
        self.target_word = None
        self.daily_number = None
        self.last_reset_date = None
        self.human_guesses = []
        self.ai_guesses = []
        self.current_turn = 'human'  # 'human' or 'ai'
        self.game_over = False
        self.winner = None

game_state = GameState()

def generate_easy_word():
    """Generate an easy-to-guess common word using LLM"""
    prompt = """Act as a word generator. Generate a single, easy-to-guess common word that would be good for a word guessing game. Requirements:
    1. Must be a common noun that everyone knows (like 'table', 'book', 'house')
    2. Must be concrete, not abstract
    3. Must be a physical object people can see and touch
    4. Must be a single word (no spaces or hyphens)
    5. Must not be a proper noun
    6. Must be between 4-8 letters
    7. Must be a word that exists in common English vocabulary
    
    Respond with ONLY the word in lowercase, no punctuation or explanation."""
    
    messages = [HumanMessage(content=prompt)]
    response = llm.invoke(messages)
    word = response.content.strip().lower()
    
    # Ensure the word exists in our model's vocabulary
    while word not in model.key_to_index:
        messages = [HumanMessage(content=prompt + "\nThe previous word was not in our vocabulary. Please try another word.")]
        response = llm.invoke(messages)
        word = response.content.strip().lower()
    
    # Print the word in the terminal for debugging/testing
    print("\n" + "="*50)
    print(f"Today's target word is: {word}")
    print("="*50 + "\n")
    
    return word

def initialize_daily_word():
    current_date = datetime.now().date()
    
    if (game_state.target_word is None or 
        game_state.last_reset_date != current_date):
        
        # Generate new easy word
        game_state.target_word = generate_easy_word()
        
        # Calculate daily number (days since epoch)
        epoch = datetime(2024, 1, 1)
        today = datetime.now()
        game_state.daily_number = (today - epoch).days
        
        game_state.last_reset_date = current_date
        game_state.human_guesses = []
        game_state.ai_guesses = []
        game_state.current_turn = 'human'
        game_state.game_over = False
        game_state.winner = None

def convert_similarity_to_rank(similarity):
    """Convert similarity score to a ranking number using the following scale:
    1.0 → Rank 1      (exact match)
    0.9 → Rank ~100   (very close)
    0.7 → Rank ~500   (somewhat close)
    0.5 → Rank ~3000  (moderately different)
    0.3 → Rank ~7000  (quite different)
    0.1 → Rank ~9999  (very different)
    """
    if similarity >= 1.0:  # Exact match
        return 1
    
    # Normalize similarity from [-1, 1] to [0, 1]
    normalized = (similarity + 1) / 2
    
    if normalized >= 0.95:  # Very close matches
        # Scale linearly from 1 to 100
        return int(1 + (100 - 1) * (1 - normalized) / 0.05)
    elif normalized >= 0.85:  # Close matches
        # Scale from 100 to 500
        return int(100 + (500 - 100) * (0.95 - normalized) / 0.1)
    elif normalized >= 0.6:  # Somewhat close
        # Scale from 500 to 3000
        return int(500 + (3000 - 500) * (0.85 - normalized) / 0.25)
    elif normalized >= 0.4:  # Moderately different
        # Scale from 3000 to 7000
        return int(3000 + (7000 - 3000) * (0.6 - normalized) / 0.2)
    else:  # Quite different to very different
        # Scale from 7000 to 9999
        return int(7000 + (9999 - 7000) * (0.4 - normalized) / 0.4)

def calculate_similarity(word1, word2):
    """Calculate semantic similarity between two words and convert to rank"""
    try:
        # Get word vectors
        vec1 = model[word1]
        vec2 = model[word2]
        
        # Calculate cosine similarity
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        
        # Convert to rank
        rank = convert_similarity_to_rank(float(similarity))
        
        return rank
    except KeyError:
        return None

@app.route('/')
def serve_index():
    return render_template('index.html')

@app.route('/api/start', methods=['POST'])
def start_game():
    initialize_daily_word()
    return jsonify({
        'status': 'success',
        'message': 'New game started'
    })

@app.route('/api/guess', methods=['POST'])
def make_guess():
    initialize_daily_word()
    
    data = request.get_json()
    guess = data.get('guess', '').lower()
    
    if not guess:
        return jsonify({'status': 'error', 'message': 'No guess provided'})
    
    if game_state.game_over:
        return jsonify({'status': 'error', 'message': 'Game is already over'})
    
    if game_state.current_turn != 'human':
        return jsonify({'status': 'error', 'message': 'Not your turn'})
    
    rank = calculate_similarity(guess, game_state.target_word)
    
    if rank is None:
        return jsonify({'status': 'error', 'message': 'Invalid word'})
    
    # Add human guess
    game_state.human_guesses.append((guess, rank))
    
    # Check if human won
    if guess == game_state.target_word:
        game_state.game_over = True
        game_state.winner = 'human'
        return jsonify({
            'status': 'success',
            'rank': rank,
            'human_guesses': game_state.human_guesses,
            'ai_guesses': game_state.ai_guesses,
            'game_over': True,
            'winner': 'human'
        })
    
    # Make AI guess
    game_state.current_turn = 'ai'
    ai_guess, ai_rank = make_ai_guess()
    
    return jsonify({
        'status': 'success',
        'rank': rank,
        'human_guesses': game_state.human_guesses,
        'ai_guesses': game_state.ai_guesses,
        'game_over': game_state.game_over,
        'winner': game_state.winner,
        'ai_guess': ai_guess,
        'ai_rank': ai_rank
    })

@app.route('/api/give-up', methods=['POST'])
def give_up():
    game_state.game_over = True
    game_state.winner = 'ai'
    return jsonify({
        'status': 'success',
        'target_word': game_state.target_word,
        'game_over': True,
        'winner': 'ai'
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    initialize_daily_word()
    return jsonify({
        'dailyNumber': game_state.daily_number,
        'totalPlayers': len(set(guess[0] for guess in game_state.human_guesses))
    })

def make_ai_guess():
    # Get all previously used words
    used_words = set(guess[0] for guess in game_state.human_guesses + game_state.ai_guesses)
    
    # Create context from previous guesses
    context = "Previous guesses and their ranks (lower is better):\n"
    for guess, rank in game_state.human_guesses + game_state.ai_guesses:
        context += f"{guess}: {rank}\n"
    
    # Add instruction to avoid used words
    context += "\nDo not use any of these words that have already been guessed: " + ", ".join(used_words)
    
    # Ask AI for a guess
    prompt = f"{context}\n\nBased on these ranks (lower is better, 1 is correct), what single word do you think is closest to the target word? The word must NOT be one that has already been guessed. Respond with just the word, no punctuation or explanation."
    
    max_attempts = 3
    for attempt in range(max_attempts):
        messages = [HumanMessage(content=prompt)]
        response = llm.invoke(messages)
        ai_guess = response.content.strip().lower()
        
        # Check if the word has been used before
        if ai_guess not in used_words:
            # Calculate similarity and add to guesses
            rank = calculate_similarity(ai_guess, game_state.target_word)
            if rank is not None:
                game_state.ai_guesses.append((ai_guess, rank))
                
                # Check if AI won
                if ai_guess == game_state.target_word:
                    game_state.game_over = True
                    game_state.winner = 'ai'
                
                game_state.current_turn = 'human'
                return ai_guess, rank
            
        # If we get here, either the word was used or invalid
        # Add to the context to explicitly tell the AI not to use this word
        context += f"\nDo not use '{ai_guess}' as it has already been guessed or is invalid."
    
    # If we've exhausted all attempts, return None
    return None, None

if __name__ == '__main__':
    app.run(debug=True)
