from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from datetime import datetime
import random
import numpy as np
from gensim.models import KeyedVectors
from langchain.schema import HumanMessage
from langchain_aws import ChatBedrockConverse
import json
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv
import boto3
import uuid
import bcrypt
from datetime import datetime
import time
from boto3.dynamodb.conditions import Key, Attr
load_dotenv(override=True)

# Set AWS credentials as environment variables
os.environ['AWS_ACCESS_KEY_ID'] = os.getenv("ACCESS_KEY_ID")
os.environ['AWS_SECRET_ACCESS_KEY'] = os.getenv("SECRET_ACCESS_KEY")

app = Flask(__name__, static_folder="static")
CORS(app)

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb',
    region_name='eu-west-3',
    aws_access_key_id=os.getenv("ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("SECRET_ACCESS_KEY")
)


# Game history functions
def save_game_history(user_id, target_word, guesses_count, final_rank, time_taken, completed=True):
    try:
        table = dynamodb.Table('ContextoGameHistory')
        timestamp = int(time.time())
        
        game_item = {
            'game_id': str(uuid.uuid4()),
            'user_id': user_id,
            'target_word': target_word,
            'guesses_count': guesses_count,
            'final_rank': final_rank,
            'played_at': timestamp,
            'completed': completed,
            'time_taken': time_taken
        }
        
        table.put_item(Item=game_item)
        return True, "Game history saved successfully"
        
    except Exception as e:
        print(f"Error saving game history: {e}")
        return False, str(e)

def get_user_game_history(user_id, limit=10):
    try:
        table = dynamodb.Table('ContextoGameHistory')
        
        # Use scan with filter expression as a temporary solution
        response = table.scan(
            FilterExpression=Attr('user_id').eq(user_id),
            Limit=limit
        )
        
        # Sort the results by played_at in descending order
        items = sorted(response['Items'], key=lambda x: x.get('played_at', 0), reverse=True)
        
        return True, items[:limit]
        
    except Exception as e:
        print(f"Error retrieving game history: {e}")
        return False, str(e)

def get_user_stats(user_id):
    try:
        table = dynamodb.Table('ContextoGameHistory')
        
        # Use scan with filter expression
        response = table.scan(
            FilterExpression=Attr('user_id').eq(user_id)
        )
        
        games = response['Items']
        
        # Calculate statistics
        total_games = len(games)
        if total_games == 0:
            return True, {
                'total_games': 0,
                'completed_games': 0,
                'completion_rate': 0,
                'best_rank': None,
                'average_guesses': 0
            }
            
        completed_games = len([g for g in games if g.get('completed', False)])
        ranks = [g.get('final_rank', float('inf')) for g in games if g.get('final_rank') is not None]
        best_rank = min(ranks) if ranks else None
        guesses = [g.get('guesses_count', 0) for g in games]
        average_guesses = sum(guesses) / len(guesses) if guesses else 0
        
        stats = {
            'total_games': total_games,
            'completed_games': completed_games,
            'completion_rate': (completed_games / total_games * 100) if total_games > 0 else 0,
            'best_rank': best_rank,
            'average_guesses': round(average_guesses, 1)
        }
        
        return True, stats
        
    except Exception as e:
        print(f"Error retrieving user stats: {e}")
        return False, str(e)

# User management functions
def create_user(username, email, password):
    try:
        table = dynamodb.Table('ContextoUsers')
        
        # Check if username already exists
        response = table.scan(
            FilterExpression=Attr('username').eq(username)
        )
        if response['Items']:
            return False, "Username already exists"
            
        # Check if email already exists
        response = table.scan(
            FilterExpression=Attr('email').eq(email)
        )
        if response['Items']:
            return False, "Email already exists"
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Create user
        user_id = str(uuid.uuid4())
        timestamp = int(time.time())
        
        user_item = {
            'user_id': user_id,
            'username': username,
            'email': email,
            'password_hash': password_hash.decode('utf-8'),
            'created_at': timestamp,
            'last_login': timestamp,
            'games_played': 0,
            'best_score': 0
        }
        
        table.put_item(Item=user_item)
        return True, "User created successfully"
        
    except Exception as e:
        print(f"Error creating user: {e}")
        return False, str(e)

def verify_user(username, password):
    try:
        table = dynamodb.Table('ContextoUsers')
        
        # Get user by username
        response = table.scan(
            FilterExpression=Attr('username').eq(username)
        )
        
        if not response['Items']:
            return False, "User not found"
            
        user = response['Items'][0]
        
        # Verify password
        if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            # Update last login
            table.update_item(
                Key={'user_id': user['user_id']},
                UpdateExpression='SET last_login = :timestamp',
                ExpressionAttributeValues={':timestamp': int(time.time())}
            )
            return True, user
        else:
            return False, "Invalid password"
            
    except Exception as e:
        print(f"Error verifying user: {e}")
        return False, str(e)

def update_user_stats(user_id, score):
    try:
        table = dynamodb.Table('ContextoUsers')
        
        # Get current user stats
        response = table.get_item(
            Key={'user_id': user_id}
        )
        
        if 'Item' not in response:
            return False, "User not found"
            
        user = response['Item']
        
        # Update stats
        table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='SET games_played = games_played + :inc, best_score = :score',
            ExpressionAttributeValues={
                ':inc': 1,
                ':score': min(score, user.get('best_score', float('inf'))) if user.get('best_score') else score
            }
        )
        return True, "Stats updated successfully"
        
    except Exception as e:
        print(f"Error updating user stats: {e}")
        return False, str(e)


# Load word embeddings model
print("Loading word embeddings model...")
model = KeyedVectors.load('glove-wiki-gigaword-300.model')
word_vectors = model.vectors
print("Model loaded!")

try:
    # Initialize ChatBedrockConverse
    llm = ChatBedrockConverse(
        model="mistral.mistral-7b-instruct-v0:2",
        temperature=0.7,
        region_name='eu-west-3'
    )

    # # Create message
    # messages = [
    #     HumanMessage(content="what's the capital of Tunisia in one word without ponctuation ?")
    # ]

    # # Get response
    # response = llm.invoke(messages)
    
    # # Print response
    # print("Response:", response.content)

except ClientError as e:
    print(f"AWS Error: {e}")
except Exception as e:
    print(f"Error: {e}")

# Game state
class GameState:
    def __init__(self):
        self.target_word = TARGET_WORDS[0] if TARGET_WORDS else None  # Initialize with first word
        self.game_over = False
        self.winner = None
        self.human_guesses = []
        self.ai_guesses = []
        self.current_turn = 'human'
        self.start_time = int(time.time())
        self.last_reset_date = datetime.now().date()  # Add last_reset_date
        self.daily_number = 0  # Add daily_number

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
    
    # Initialize if target_word is None or last_reset_date is different from current date
    if (game_state.target_word is None or 
        getattr(game_state, 'last_reset_date', None) != current_date):
        
        # Generate new easy word
        game_state.target_word = generate_easy_word()
        
        # Calculate daily number (days since epoch)
        epoch = datetime(2024, 1, 1)
        today = datetime.now()
        game_state.daily_number = (today - epoch).days
        
        game_state.last_reset_date = current_date
        game_state.human_guesses = []  # Create new empty list
        game_state.ai_guesses = []     # Create new empty list
        game_state.current_turn = 'human'
        game_state.game_over = False
        game_state.winner = None
        game_state.start_time = int(time.time())

def convert_similarity_to_rank(similarity):
    """Convert similarity score to a ranking number using the following scale:
    1.0 → Rank 1      (exact match)
    0.9 → Rank ~100   (very close)
    0.7 → Rank ~300   (somewhat close)
    0.5 → Rank ~500   (moderately different)
    0.3 → Rank ~700   (quite different)
    0.1 → Rank ~900   (very different)
    """
    # Ensure similarity is between 0 and 1
    similarity = max(0.0, min(1.0, similarity))
    
    if similarity == 1.0:
        return 1
    
    # Convert to rank between 1 and 1000 (inverted)
    rank = int(1000 - (similarity * 1000))
    
    # Ensure rank is at least 2 (since 1 is reserved for exact match)
    rank = max(2, rank)
    
    return rank

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
        
        return rank, float(similarity)
    except KeyError:
        return None

# Helper function to get leaderboard data
def get_leaderboard_data():
    # Combine and sort all guesses
    all_guesses = []
    
    # Add human guesses
    for word, rank, similarity in game_state.human_guesses:
        all_guesses.append({
            'word': word,
            'rank': rank,
            'player': 'human'
        })
    
    # Add AI guesses
    for word, rank, similarity in game_state.ai_guesses:
        all_guesses.append({
            'word': word,
            'rank': rank,
            'player': 'ai'
        })
    
    # Sort by rank (lower is better)
    all_guesses.sort(key=lambda x: x['rank'])
    
    return {
        'leaderboard': all_guesses,
        'totalGuesses': len(all_guesses),
        'totalPlayers': len(set(guess['player'] for guess in all_guesses))
    }

@app.route('/')
def serve_index():
    return render_template('index.html')

@app.route('/api/start', methods=['POST'])
def start_game():
    initialize_daily_word()  # Initialize or get the daily word
    
    # Reset game state with new empty lists
    game_state.human_guesses = []  # Create new empty list
    game_state.ai_guesses = []     # Create new empty list
    game_state.current_turn = 'human'
    game_state.game_over = False
    game_state.winner = None
    game_state.start_time = int(time.time())
    
    # Return empty leaderboard
    return jsonify({
        'status': 'success',
        'leaderboard': {
            'leaderboard': [],
            'totalGuesses': 0,
            'totalPlayers': 0
        }
    })

@app.route('/api/guess', methods=['POST'])
def make_guess():
    data = request.get_json()
    guess = data.get('guess', '').lower()
    user_id = data.get('user_id')
    
    if not guess:
        return jsonify({'status': 'error', 'message': 'No guess provided'})
    
    if game_state.game_over:
        return jsonify({'status': 'error', 'message': 'Game is already over'})
    
    if game_state.current_turn != 'human':
        return jsonify({'status': 'error', 'message': 'Not your turn'})
    
    # Check if word has been guessed before - fixed to check entire words
    used_words = {g[0] for g in game_state.human_guesses + game_state.ai_guesses}  # g[0] is the word from the tuple
    if guess in used_words:
        return jsonify({'status': 'error', 'message': 'Word has already been guessed'})
    
    rank, similarity = calculate_similarity(guess, game_state.target_word)
    print("Guess:"+ guess + " similarity:" + str(similarity))
    
    if rank is None:
        return jsonify({'status': 'error', 'message': 'Invalid word'})
    
    # Add human guess
    game_state.human_guesses.append((guess, rank, float(similarity)))
    
    # Check if human won
    if rank == 1:
        game_state.game_over = True
        game_state.winner = 'human'
        if user_id:
            save_game_history(
                user_id=user_id,
                target_word=game_state.target_word,
                guesses_count=len(game_state.human_guesses),
                final_rank=1,
                time_taken=int(time.time()) - game_state.start_time,
                completed=True
            )
        return jsonify({
            'status': 'success',
            'rank': rank,
            'game_over': True,
            'winner': 'human',
            'target_word': game_state.target_word,
            'leaderboard': get_leaderboard_data()  # Return current leaderboard data
        })
    
    # If human didn't win, let AI make a guess
    if not game_state.game_over:
        game_state.current_turn = 'ai'
        ai_guess, ai_rank = make_ai_guess()
        
        if ai_guess is None:
            return jsonify({
                'status': 'success',
                'rank': rank,
                'game_over': game_state.game_over,
                'winner': game_state.winner,
                'ai_guess': None,
                'ai_rank': None,
                'leaderboard': get_leaderboard_data()  # Return current leaderboard data
            })
    
    # Always switch back to human turn after AI's guess (unless game is over)
    if not game_state.game_over:
        game_state.current_turn = 'human'
    
    return jsonify({
        'status': 'success',
        'rank': rank,
        'game_over': game_state.game_over,
        'winner': game_state.winner,
        'ai_guess': ai_guess,
        'ai_rank': ai_rank,
        'target_word': game_state.target_word if game_state.game_over else None,
        'leaderboard': get_leaderboard_data()  # Return current leaderboard data
    })

@app.route('/api/give-up', methods=['POST'])
def give_up():
    data = request.get_json()
    user_id = data.get('user_id')
    
    if user_id:
        # Save game history as incomplete
        guesses_count = len(game_state.human_guesses)
        time_taken = int(time.time()) - game_state.start_time
        last_rank = guesses_count + 1  # Use number of guesses + 1 as final rank for incomplete games
        
        save_game_history(
            user_id=user_id,
            target_word=game_state.target_word,
            guesses_count=guesses_count,
            final_rank=last_rank,
            time_taken=time_taken,
            completed=False
        )

    game_state.game_over = True
    game_state.winner = 'ai'
    return jsonify({
        'target_word': game_state.target_word,
        'total_guesses': len(game_state.human_guesses)
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    initialize_daily_word()
    return jsonify({
        'dailyNumber': game_state.daily_number,
        'totalPlayers': len(set(guess[0] for guess in game_state.human_guesses))
    })

@app.route('/api/save_game', methods=['POST'])
def save_game():
    data = request.get_json()
    required_fields = ['user_id', 'target_word', 'guesses_count', 'final_rank', 'time_taken', 'completed']
    
    if not all(field in data for field in required_fields):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
    success, message = save_game_history(
        data['user_id'],
        data['target_word'],
        data['guesses_count'],
        data['final_rank'],
        data['time_taken'],
        data['completed']
    )
    
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 500

@app.route('/api/available-words', methods=['GET'])
def get_available_words():
    return jsonify({
        'words': [f'Word {i+1}' for i in range(len(TARGET_WORDS))],
        'count': len(TARGET_WORDS)
    })

@app.route('/api/set-target-word', methods=['POST'])
def set_target_word():
    data = request.get_json()
    word_index = data.get('index')
    
    if word_index is None or not (0 <= word_index < len(TARGET_WORDS)):
        return jsonify({'success': False, 'message': 'Invalid word index'}), 400
    
    # Initialize new game state
    selected_word = TARGET_WORDS[word_index]
    print(f"\n=== New Game Started ===")
    print(f"Selected Word: {selected_word}")
    print("=" * 25)
    
    # Clear all game state
    game_state.target_word = selected_word
    game_state.game_over = False
    game_state.winner = None
    game_state.human_guesses = []  # Create new empty list
    game_state.ai_guesses = []     # Create new empty list
    game_state.current_turn = 'human'
    game_state.start_time = int(time.time())
    
    # Return empty leaderboard for frontend sync
    return jsonify({
        'success': True,
        'leaderboard': {
            'leaderboard': [],
            'totalGuesses': 0,
            'totalPlayers': 0
        }
    })

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    return jsonify(get_leaderboard_data())

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not all([username, email, password]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
    success, message = create_user(username, email, password)
    return jsonify({'success': success, 'message': message})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not all([username, password]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
    success, result = verify_user(username, password)
    if success:
        return jsonify({
            'success': True,
            'user': {
                'user_id': result['user_id'],
                'username': result['username'],
                'email': result['email'],
                'games_played': result['games_played'],
                'best_score': result['best_score']
            }
        })
    else:
        return jsonify({'success': False, 'message': result}), 401

@app.route('/api/update_stats', methods=['POST'])
def update_stats():
    data = request.get_json()
    user_id = data.get('user_id')
    score = data.get('score')
    
    if not all([user_id, score]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
    success, message = update_user_stats(user_id, score)
    return jsonify({'success': success, 'message': message})

@app.route('/api/game_history', methods=['GET'])
def get_history():
    user_id = request.args.get('user_id')
    limit = int(request.args.get('limit', 10))
    
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID is required'}), 400
        
    success, result = get_user_game_history(user_id, limit)
    if success:
        return jsonify({'success': True, 'history': result})
    else:
        return jsonify({'success': False, 'message': result}), 500

@app.route('/api/user_stats', methods=['GET'])
def get_user_game_stats():
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID is required'}), 400
        
    success, result = get_user_stats(user_id)
    if success:
        return jsonify({'success': True, 'stats': result})
    else:
        return jsonify({'success': False, 'message': result}), 500

def make_ai_guess():
    # Get all previously used words
    used_words = {guess[0] for guess in game_state.human_guesses + game_state.ai_guesses}
    print("Used words:", used_words)
    # Create context from previous guesses, sorted by rank to help AI understand the pattern
    all_guesses = game_state.human_guesses + game_state.ai_guesses
    sorted_guesses = sorted(all_guesses, key=lambda x: x[1])  # Sort by rank (second element)
    print("sorted guesses:", sorted_guesses)
    
    # Take only the 10 most relevant guesses to avoid context overload
    relevant_guesses = sorted_guesses[:10]
    print("relevant guesses:", relevant_guesses)
    context = " "
    context = '''
    This is like the Contexto word guessing game. You need to guess a target word based on semantic similarity.
    Each guess gets a similarity score from 0 to 1 \n'''
    context += "Previous guesses and their similarities (higher is better):\n"
    for guess, rank, similarity in relevant_guesses:
        context += f"{guess} (similarity {similarity:.3f})\n"
    print("context:", context)
    
    # Add instruction to avoid used words
    context += "\nDo not use any of these words that have already been guessed: " + ", ".join(used_words)
    
    # Ask AI for a guess with more specific instructions
    prompt = f"{context}\n\nBased on these similarities (higher is better, 1 is correct), suggest a single word that you think is closest to the target word. Requirements:\n1. Must be a common English word\n2. Must NOT be any word that has been guessed before\n3. Should try to get a better similarity than {sorted_guesses[0][2] if sorted_guesses else 'previous guesses'}\n\nRespond with just the word, no punctuation or explanation."
    
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
            rank, similarity = calculate_similarity(ai_guess, game_state.target_word)
            print("similarity:", similarity)
            if rank is not None:
                game_state.ai_guesses.append((ai_guess, rank, float(similarity)))
                
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
