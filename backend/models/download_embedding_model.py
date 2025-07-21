from sentence_transformers import SentenceTransformer
import os
import shutil

model_path = "models/vietnamese-bi-encoder"
try:
    print("Downloading bkai-foundation-models/vietnamese-bi-encoder model...")
    model = SentenceTransformer('bkai-foundation-models/vietnamese-bi-encoder')
    
    print("Saving model...")
    model.save(model_path)
    
    print("Model downloaded and saved successfully!")
    
    # Test model
    print("Testing model...")
    test_text = ["Xin chào", "Hello world"]
    embeddings = model.encode(test_text)
    print(f"Model test successful! Embedding shape: {embeddings.shape}")
    
except Exception as e:
    print(f"Error: {e}")