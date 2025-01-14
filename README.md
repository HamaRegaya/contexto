![Alt text](https://imgur.com/ox8zuD0.png)

# Cognify: Human vs AI Word Guessing Game

![Alt text](https://i.imgur.com/8TqyO0C.png)

Cognify is an engaging word guessing game where players compete against an AI to guess a target word. The game uses GloVe word embeddings to calculate the similarity between words, providing feedback on how close each guess is to the target word. The game features a Flask-based backend and a JavaScript frontend, offering an interactive and educational experience.


![Alt text](https://imgur.com/mH1OXts.png)

## Repository Structure

```
.
├── amplify.yml
├── app.py
├── build.sh
├── Dockerfile
├── dynamodb.py
├── embedding.py
├── game.py
├── glove-wiki.py
├── LLM.py
├── Procfile
├── README.md
├── requirements.txt
├── similarity.py
├── static
│   ├── app.js
│   ├── sounds
│   │   └── README.md
│   └── styles.css
├── templates
│   └── index.html
└── glove-wiki-gigaword-50.model
```

### Key Files:

- `amplify.yml`: Configuration file for AWS Amplify.
- `app.py`: Flask application serving as the backend for the word guessing game.
- `build.sh`: Script to build the Flask application.
- `Dockerfile`: Docker configuration for containerizing the application.
- `dynamodb.py`: Script to create DynamoDB tables for user and game history.
- `embedding.py`: Script to generate embeddings using Amazon Titan Text Embeddings.
- `game.py`: Utility script for word similarity calculations using GloVe embeddings.
- `glove-wiki.py`: Script to download and save the pre-trained GloVe word embedding model.
- `LLM.py`: Script to initialize and use the ChatBedrockConverse model.
- `Procfile`: Configuration for deploying the application with Gunicorn.
- `README.md`: This file, providing an overview of the project.
- `requirements.txt`: List of Python dependencies for the project.
- `similarity.py`: Script for calculating word similarity scores.
- `static/app.js`: Frontend JavaScript code for game interaction and UI updates.
- `static/sounds/README.md`: Instructions for downloading sound effects.
- `static/styles.css`: CSS styles for the game's web interface.
- `templates/index.html`: HTML template for the game's web interface.
- `glove-wiki-gigaword-50.model`: Pre-trained GloVe word embedding model.

## Technologies Used
![Alt text](https://learnersmind.com/storage/resources/cD7xI0qVAestQGqFSSzawJZoLS5ZOvRYQcQtfOsE.png)
### Deployment Technologies

- **Docker**: Used for containerizing the application, ensuring consistency across different environments.
- **EC2**: Amazon Elastic Compute Cloud (EC2) instances are used to host the application.
- **Route 53**: Amazon Route 53 is used for domain name system (DNS) web service.
- **CloudFormation**: AWS CloudFormation is used to set up and manage the infrastructure as code.
- **Elastic Container Registry (ECR)**: Amazon ECR is used to store, manage, and deploy Docker container images.
- **Elastic Container Service (ECS)**: Amazon ECS is used to run and manage Docker containers on a cluster of EC2 instances.

### Machine Learning Models
![Alt text](https://miro.medium.com/v2/resize:fit:800/0*Pt35xx4zGH-4SQmF.png)
- **Amazon Bedrock Models**:
  - **LLM**: The game uses Amazon Bedrock models for large language models (LLM). Specifically, the `mistral.mistral-7b-instruct-v0:2` model is used.
  - **Embeddings**: For generating text embeddings, the `amazon.titan-embed-text-v2:0` model is used.

### Additional Technologies
![Alt text](https://devio2023-media.developers.io/wp-content/uploads/2024/04/langchain-bedrock-1200x630-1.png)
- **Flask**: A lightweight WSGI web application framework used for the backend.
- **Gensim**: A Python library for topic modeling and document similarity analysis.
- **scikit-learn**: A machine learning library for Python used for various machine learning tasks.
- **python-dotenv**: Reads key-value pairs from a `.env` file and can set them as environment variables.
- **Flask-SQLAlchemy**: Adds SQLAlchemy support to Flask applications.
- **Flask-Cors**: A Flask extension for handling Cross Origin Resource Sharing (CORS), making cross-origin AJAX possible.
- **gunicorn**: A Python WSGI HTTP Server for UNIX used to serve the Flask application.
- **langchain-aws**: A library to integrate LangChain with AWS services.
- **langchain**: A framework for developing applications powered by language models.
- **gevent**: A coroutine-based Python networking library that uses greenlet to provide a high-level synchronous API.
- **boto3**: The Amazon Web Services (AWS) SDK for Python, which allows Python developers to write software that makes use of Amazon services.
- **bcrypt**: A library to hash and check passwords.
- **python-jose**: A JavaScript Object Signing and Encryption (JOSE) implementation in Python.
- **waitress**: A pure-Python WSGI server for serving Python web applications.



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
    "guess": "example"
  }
  ```
  Response:
  ```json
  {
    "status": "success",
    "rank": 123,
    "game_over": false,
    "winner": null,
    "ai_guess": "sample",
    "ai_rank": 456,
    "target_word": null,
    "leaderboard": {
      "leaderboard": [],
      "totalGuesses": 0,
      "totalPlayers": 0
    }
  }
  ```

- `POST /api/give-up`: Reveal the target word
  Response:
  ```json
  {
    "target_word": "target",
    "total_guesses": 10
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

- `POST /api/start`: Start a new game
  Response:
  ```json
  {
    "status": "success",
    "leaderboard": {
      "leaderboard": [],
      "totalGuesses": 0,
      "totalPlayers": 0
    }
  }
  ```

- `POST /api/save_game`: Save game history
  ```json
  {
    "user_id": "user123",
    "target_word": "target",
    "guesses_count": 10,
    "final_rank": 1,
    "time_taken": 300,
    "completed": true
  }
  ```
  Response:
  ```json
  {
    "success": true,
    "message": "Game history saved successfully"
  }
  ```

- `GET /api/game_history`: Retrieve user game history
  ```json
  {
    "user_id": "user123",
    "limit": 10
  }
  ```
  Response:
  ```json
  {
    "success": true,
    "history": [
      {
        "game_id": "game123",
        "user_id": "user123",
        "target_word": "target",
        "guesses_count": 10,
        "final_rank": 1,
        "played_at": 1620000000,
        "completed": true,
        "time_taken": 300
      }
    ]
  }
  ```

- `GET /api/user_stats`: Retrieve user statistics
  ```json
  {
    "user_id": "user123"
  }
  ```
  Response:
  ```json
  {
    "success": true,
    "stats": {
      "total_games": 10,
      "completed_games": 8,
      "completion_rate": 80,
      "best_rank": 1,
      "average_guesses": 5.5
    }
  }
  ```

### Troubleshooting

1. **Model not found error**:
   - Ensure you've run `python glove-wiki.py` to download the GloVe model.
   - Verify that `glove-wiki-gigaword-50.model` exists in the project root.

2. **Word not in dictionary error**:
   - The GloVe model has a limited vocabulary. Try using more common words.

3. **Slow response times**:
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
