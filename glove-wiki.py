import gensim.downloader as api

# Path to save the model
MODEL_PATH = "glove-wiki-gigaword-300.model"

# Download and save the model
def download_and_save_model():
    print("Downloading the model...")
    model = api.load("glove-wiki-gigaword-300")  # GloVe with 50 dimensions
    model.save(MODEL_PATH)
    print(f"Model saved locally as '{MODEL_PATH}'.")

if __name__ == "__main__":
    download_and_save_model()