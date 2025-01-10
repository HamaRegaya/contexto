# Word Guessing Game with GloVe Word Embeddings

This project implements a daily word guessing game using GloVe word embeddings to calculate similarity between words. Players attempt to guess a target word, receiving feedback on how similar their guesses are to the correct answer.

The game features a Flask-based backend that handles word similarity calculations and game logic, and a JavaScript frontend that provides an interactive user interface. The application uses pre-trained GloVe (Global Vectors for Word Representation) word embeddings to compute semantic similarities between words, offering an engaging and educational word game experience.

## Repository Structure

```
.
├── app.py
├── game.py
├── glove-wiki.py
├── static
│   ├── app.js
│   └── styles.css
└── templates
    └── index.html
```

### Key Files:

- `app.py`: Flask application serving as the backend for the word guessing game.
- `game.py`: Utility script for word similarity calculations using GloVe embeddings.
- `glove-wiki.py`: Script to download and save the pre-trained GloVe word embedding model.
- `static/app.js`: Frontend JavaScript code for game interaction and UI updates.
- `templates/index.html`: HTML template for the game's web interface.

## Usage Instructions

### Installation

1. Ensure you have Python 3.7+ installed.
2. Clone the repository to your local machine.
3. Install required Python packages:
   ```
   pip install -r requirements.txt
   ```
4. Download the GloVe model by running:
   ```
   python glove-wiki.py
   ```

### Getting Started

1. Start the Flask server:
   ```
   python app.py
   ```
2. Open a web browser and navigate to `http://localhost:5000` to play the game.

### Game Rules

- A new target word is selected daily.
- Enter your guess in the input field and submit.
- The game will show the similarity percentage between your guess and the target word.
- Keep guessing until you find the correct word or choose to give up.

### API Endpoints

- `POST /api/guess`: Submit a word guess
  ```json
  {
    "word": "example"
  }
  ```
  Response:
  ```json
  {
    "similarity": 0.75,
    "isCorrect": false,
    "dailyNumber": 42
  }
  ```

- `POST /api/give-up`: Reveal the target word
  Response:
  ```json
  {
    "word": "target",
    "dailyNumber": 42,
    "message": "The word was: target"
  }
  ```

- `GET /api/stats`: Retrieve game statistics
  Response:
  ```json
  {
    "dailyNumber": 42,
    "totalPlayers": 3500
  }
  ```

### Troubleshooting

1. Model not found error:
   - Ensure you've run `python glove-wiki.py` to download the GloVe model.
   - Verify that `glove-wiki-gigaword-50.model` exists in the project root.

2. Word not in dictionary error:
   - The GloVe model has a limited vocabulary. Try using more common words.

3. Slow response times:
   - The first request might be slow as the model loads into memory. Subsequent requests should be faster.

### Debugging

To enable debug mode, set the `FLASK_ENV` environment variable:

```
export FLASK_ENV=development
```

This will provide more detailed error messages and enable auto-reloading of the Flask application.

## Data Flow

The word guessing game follows this data flow:

1. User enters a guess in the frontend (app.js).
2. The guess is sent to the backend (/api/guess endpoint in app.py).
3. The backend loads the GloVe model (if not already loaded) and calculates the similarity between the guess and the target word.
4. The similarity score and correctness are sent back to the frontend.
5. The frontend updates the UI with the guess result and similarity score.

```
[User Input] -> [Frontend (app.js)] -> [Backend (app.py)] -> [GloVe Model] 
                                                          -> [Similarity Calculation]
                                                          -> [Backend Response]
              <- [Frontend Update]   <- [JSON Response]
```

Note: The target word is reset daily on the server-side, ensuring all players guess the same word each day.