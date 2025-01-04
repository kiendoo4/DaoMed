from sentence_transformers import SentenceTransformer

# Load the model from the local directory
model = SentenceTransformer('model/vietnamese-bi-encoder')  # Using the model from local machine

# Example sentence for encoding
sentence = "Xin chào Việt Nam"

# Get the embedding for the sentence
embedding = model.encode(sentence)

# Print the resulting embeddings
print(embedding)
