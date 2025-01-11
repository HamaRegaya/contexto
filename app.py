from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from datetime import datetime
import random
import numpy as np
from gensim.models import KeyedVectors
from langchain.schema import HumanMessage
from LLM import llm

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

# Static list of simple words to guess
TARGET_WORDS = [
    'house', 'table', 'chair', 'book', 'phone',
    'water', 'bread', 'shoes', 'clock', 'door',
    'paper', 'glass', 'plate', 'shirt', 'light',
    'music', 'plant', 'apple', 'knife', 'spoon',
    'pencil', 'window', 'bottle', 'flower', 'camera',
    'pillow', 'coffee', 'mirror', 'carpet', 'picture'
]

game_state = GameState()

def generate_easy_word():
    """Select a random word from our predefined list"""
    word = random.choice(TARGET_WORDS)
    
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
    
    # Check if word has been guessed before
    used_words = {guess[0] for guess in game_state.human_guesses + game_state.ai_guesses}
    if guess in used_words:
        return jsonify({'status': 'error', 'message': 'Word has already been guessed'})
    
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
    
    # If AI couldn't make a valid guess, switch back to human turn
    if ai_guess is None:
        game_state.current_turn = 'human'
        return jsonify({
            'status': 'success',
            'rank': rank,
            'human_guesses': game_state.human_guesses,
            'ai_guesses': game_state.ai_guesses,
            'game_over': game_state.game_over,
            'winner': game_state.winner,
            'ai_guess': None,
            'ai_rank': None
        })
    
    # Always switch back to human turn after AI's guess (unless game is over)
    if not game_state.game_over:
        game_state.current_turn = 'human'
    
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
    used_words = {guess[0] for guess in game_state.human_guesses + game_state.ai_guesses}
    
    # Create context from previous guesses, sorted by rank to help AI understand the pattern
    all_guesses = game_state.human_guesses + game_state.ai_guesses
    sorted_guesses = sorted(all_guesses, key=lambda x: x[1])  # Sort by rank
    
    # Take only the 10 most relevant guesses to avoid context overload
    relevant_guesses = sorted_guesses[:10]
    
    context = "Previous guesses and their ranks (lower is better):\n"
    for guess, rank in relevant_guesses:
        context += f"{guess} (rank {rank})\n"
    
    if sorted_guesses:
        best_rank = sorted_guesses[0][1]
        context += f"\nThe best guess so far had rank {best_rank}. Try to find a word that would get an even better rank."
    
    # Add instruction to avoid used words
    context += "\nDo not use any of these words that have already been guessed: " + ", ".join(used_words)
    
    # Ask AI for a guess with more specific instructions
    prompt = f"{context}\n\nBased on these ranks (lower is better, 1 is correct), suggest a single word that you think is closest to the target word. Requirements:\n1. Must be a common English word\n2. Must NOT be any word that has been guessed before\n3. Should try to get a better rank than {best_rank if sorted_guesses else 'previous guesses'}\n\nRespond with just the word, no punctuation or explanation."
    
    max_attempts = 5  # Increased attempts
    for attempt in range(max_attempts):
        messages = [HumanMessage(content=prompt)]
        response = llm.invoke(messages)
        ai_guess = response.content.strip().lower()
        
        # Validate the guess
        if (ai_guess not in used_words and 
            ai_guess in model.key_to_index and 
            len(ai_guess) >= 2):  # Basic validation
            
            # Calculate similarity and add to guesses
            rank = calculate_similarity(ai_guess, game_state.target_word)
            if rank is not None:
                game_state.ai_guesses.append((ai_guess, rank))
                
                # Check if AI won
                if ai_guess == game_state.target_word:
                    game_state.game_over = True
                    game_state.winner = 'ai'
                
                return ai_guess, rank
        
        # If we get here, either the word was used or invalid
        # Add to the context to explicitly tell the AI not to use this word
        context += f"\nDo not use '{ai_guess}' as it has already been guessed or is invalid."
        prompt = context + "\n\nTry another word. Respond with just the word, no punctuation or explanation."
    
    # If we've exhausted all attempts, return None
    return None, None

if __name__ == '__main__':
    app.run(debug=True)
