import numpy as np
import pandas as pd
from gensim.models import Word2Vec

# Load OHLC data from a CSV file
# The CSV file should have columns: ['timestamp', 'open', 'high', 'low', 'close']
df = pd.read_csv('ohlc_data.csv')

# Preprocessing: Calculate price movements as a sequence of directional changes
# Here we represent movements as 'up', 'down', or 'flat'
def calculate_movement(open_price, close_price):
    if close_price > open_price:
        return 'up'
    elif close_price < open_price:
        return 'down'
    else:
        return 'flat'

df['movement'] = df.apply(lambda row: calculate_movement(row['open'], row['close']), axis=1)

# Create sequences of movements
# Group movements into sequences of a specific length (e.g., 10 movements per sequence)
sequence_length = 10
sequences = []

for i in range(len(df) - sequence_length):
    sequence = df['movement'].iloc[i:i + sequence_length].tolist()
    sequences.append(sequence)

# Train Word2Vec model
model = Word2Vec(sentences=sequences, vector_size=50, window=5, min_count=1, sg=1, workers=4)

# Save the model for later use
model.save("word2vec_ohlc.model")

# Example: Get the vector for a movement
movement_vector = model.wv['up']
print(f"Vector for 'up': {movement_vector}")

# Example: Find the most similar movements to 'up'
similar_movements = model.wv.most_similar('up', topn=3)
print(f"Most similar movements to 'up': {similar_movements}")

