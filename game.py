from flask import Flask, jsonify, request
import random
from datetime import datetime, timedelta
import numpy as np
from LLM import llm
from langchain_core.messages import HumanMessage

app = Flask(__name__)

class Game:
    def __init__(self):
        self.target_word = None
        self.human_guesses = []
        self.ai_guesses = []
        self.game_over = False
        self.winner = None
        self.current_turn = 'human'  # 'human' or 'ai'
        
        # Load word embeddings
        self.word_embeddings = np.load('word_embeddings.npy', allow_pickle=True).item()
        self.words = list(self.word_embeddings.keys())
        
    def start_new_game(self):
        self.target_word = random.choice(self.words)
        self.human_guesses = []
        self.ai_guesses = []
        self.game_over = False
        self.winner = None
        self.current_turn = 'human'
        return self.target_word
    
    def calculate_similarity(self, word1, word2):
        if word1 not in self.word_embeddings or word2 not in self.word_embeddings:
            return 0.0
        vec1 = self.word_embeddings[word1]
        vec2 = self.word_embeddings[word2]
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
    
    def make_ai_guess(self):
        # Create context from previous guesses
        context = "Previous guesses and their similarities:\n"
        for guess, similarity in self.human_guesses + self.ai_guesses:
            context += f"{guess}: {similarity}\n"
        
        # Ask AI for a guess
        prompt = f"{context}\nBased on these similarities, what single word do you think is closest to the target word? Respond with just the word, no punctuation or explanation."
        messages = [HumanMessage(content=prompt)]
        response = llm.invoke(messages)
        ai_guess = response.content.strip().lower()
        
        # Calculate similarity and add to guesses
        similarity = self.calculate_similarity(ai_guess, self.target_word)
        self.ai_guesses.append((ai_guess, similarity))
        
        # Check if AI won
        if ai_guess == self.target_word:
            self.game_over = True
            self.winner = 'ai'
        
        self.current_turn = 'human'
        return ai_guess, similarity
    
    def make_human_guess(self, guess):
        guess = guess.lower().strip()
        similarity = self.calculate_similarity(guess, self.target_word)
        self.human_guesses.append((guess, similarity))
        
        # Check if human won
        if guess == self.target_word:
            self.game_over = True
            self.winner = 'human'
        
        self.current_turn = 'ai'
        return similarity

game = Game()

@app.route('/api/start', methods=['POST'])
def start_game():
    target_word = game.start_new_game()
    return jsonify({
        'status': 'success',
        'message': 'New game started'
    })

@app.route('/api/guess', methods=['POST'])
def make_guess():
    data = request.get_json()
    guess = data.get('guess', '').lower().strip()
    
    if game.game_over:
        return jsonify({
            'status': 'error',
            'message': 'Game is already over'
        })
    
    if game.current_turn != 'human':
        return jsonify({
            'status': 'error',
            'message': 'Not your turn'
        })
    
    # Process human guess
    similarity = game.make_human_guess(guess)
    
    response_data = {
        'status': 'success',
        'similarity': similarity,
        'human_guesses': game.human_guesses,
        'ai_guesses': game.ai_guesses,
        'game_over': game.game_over,
        'winner': game.winner
    }
    
    # If game is not over, make AI guess
    if not game.game_over:
        ai_guess, ai_similarity = game.make_ai_guess()
        response_data.update({
            'ai_guess': ai_guess,
            'ai_similarity': ai_similarity,
            'game_over': game.game_over,
            'winner': game.winner
        })
    
    return jsonify(response_data)

@app.route('/api/give-up', methods=['POST'])
def give_up():
    game.game_over = True
    game.winner = 'ai'
    return jsonify({
        'status': 'success',
        'target_word': game.target_word,
        'game_over': True,
        'winner': 'ai'
    })

if __name__ == '__main__':
    app.run(debug=True)