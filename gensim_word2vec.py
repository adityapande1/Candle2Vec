from gensim.models import Word2Vec

# Example sequences of price movements (replace with actual sequences)
sequences = [
    ['up', 'down', 'flat', 'up', 'down'],
    ['flat', 'up', 'down', 'up', 'flat'],
    ['down', 'down', 'up', 'up', 'flat'],
    # Add more sequences here...
]

# Initialize and train the Word2Vec model
model = Word2Vec(sentences=sequences, vector_size=50, window=5, min_count=1, sg=1, workers=4)

# Save the trained model
model.save("word2vec_ohlc.model")

# Example usage: Retrieve the vector for a specific movement
movement_vector = model.wv['up']
print(f"Vector for 'up': {movement_vector}")

# Example usage: Find the most similar movements to 'up'
similar_movements = model.wv.most_similar('up', topn=3)
print(f"Most similar movements to 'up': {similar_movements}")
