# Bigram Language Model: Explanation

## Overview

This document explains the process and purpose of the `bigram.py` and `bigram-v2.py` scripts. Both scripts implement a bigram-based language model using PyTorch. The bigram model predicts the next character in a sequence based on the current character, making it a simple yet effective approach to language modeling.

---

## `bigram.py`

### What It Does

The `bigram.py` script implements a basic bigram language model. It trains on a text dataset to predict the next character given the current one. The model uses a simple embedding layer to map characters to logits for prediction.

### How It Works

1. **Data Preparation**:
   - Reads a text file (`input.txt`) and extracts unique characters.
   - Encodes characters into integers for processing.
   - Splits the data into training and validation sets (90% train, 10% validation).

2. **Model Definition**:
   - The `BigramLanguageModel` class contains:
     - An embedding layer (`nn.Embedding`) to map characters to logits.
     - A `forward` method to compute logits and loss.
     - A `generate` method to produce text by sampling from the model's predictions.

3. **Training**:
   - Uses the AdamW optimizer to minimize cross-entropy loss.
   - Periodically evaluates the model on validation data.

4. **Text Generation**:
   - Starts with a context (e.g., a single character) and generates new characters iteratively.

### Why It Works

The bigram model captures simple dependencies between consecutive characters. While limited in scope, it demonstrates the core principles of language modeling and serves as a foundation for more complex models.

---

## `bigram-v2.py`

### What It Does

The `bigram-v2.py` script extends the functionality of `bigram.py` by introducing self-attention mechanisms. This allows the model to consider longer contexts when making predictions, improving its ability to capture patterns in the data.

### How It Works

1. **Data Preparation**:
   - Similar to `bigram.py`, but includes additional hyperparameters for context length (`block_size`) and embedding dimensions (`n_embd`).

2. **Model Definition**:
   - The `BigramLanguageModel` class is enhanced with:
     - Token and position embeddings to represent input sequences.
     - A self-attention head (`Head` class) to compute attention scores and aggregate information.
     - A linear layer (`lm_head`) to map embeddings to logits.

3. **Training**:
   - Similar to `bigram.py`, but with additional complexity due to the self-attention mechanism.

4. **Text Generation**:
   - Similar to `bigram.py`, but benefits from the model's improved ability to capture context.

### Why It Works

By incorporating self-attention, the model can consider longer contexts when making predictions. This improves its ability to generate coherent text and capture patterns in the data.

---

## Key Differences

| Feature              | `bigram.py`                | `bigram-v2.py`            |
| -------------------- | -------------------------- | ------------------------- |
| Context Length       | 1 (current character only) | Up to `block_size` tokens |
| Embedding Dimensions | Equal to vocabulary size   | Configurable (`n_embd`)   |
| Self-Attention       | No                         | Yes                       |
| Position Embeddings  | No                         | Yes                       |

---

## Conclusion

Both scripts demonstrate the principles of language modeling using bigrams. While `bigram.py` provides a simple implementation, `bigram-v2.py` introduces self-attention to improve performance. These scripts serve as valuable learning tools for understanding language modeling and neural network design.
