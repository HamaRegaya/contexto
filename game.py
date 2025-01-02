from gensim.models import KeyedVectors
from sklearn.metrics.pairwise import cosine_similarity
import os
import numpy as np

# Path to the saved model
MODEL_PATH = "glove-wiki-gigaword-50.model"

# Load the model - only do this once
model = None

def load_model():
    global model
    if model is not None:
        return model
    
    if os.path.exists(MODEL_PATH):
        print("Loading the model from local storage...")
        model = KeyedVectors.load(MODEL_PATH)
        # Preload vectors into memory for faster access
        model.fill_norms()
        print("Model loaded successfully!")
        return model
    else:
        raise FileNotFoundError(f"Model file '{MODEL_PATH}' not found.")

def calculate_word_similarity(model, word1, word2):
    try:
        # Using numpy's dot product and norm is faster than sklearn's cosine_similarity
        return np.dot(model[word1], model[word2]) / (np.linalg.norm(model[word1]) * np.linalg.norm(model[word2]))
    except KeyError as e:
        return f"Word not found in vocabulary: {str(e)}"

def main():
    model = load_model()
    
    while True:
        try:
            word1 = input("Enter the first word (or 'q' to quit): ").lower().strip()
            if word1 == 'q':
                break
                
            word2 = input("Enter the second word: ").lower().strip()
            
            similarity_score = calculate_word_similarity(model, word1, word2)
            if isinstance(similarity_score, str):
                print(similarity_score)
            else:
                print(f"Similarity: {similarity_score:.4f}")
                
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
