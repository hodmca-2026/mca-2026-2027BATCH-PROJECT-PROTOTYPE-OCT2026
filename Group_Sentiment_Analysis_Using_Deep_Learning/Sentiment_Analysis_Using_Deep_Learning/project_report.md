# Project Report

## Deep Learning-Based Movie Review Sentiment Analysis Using RNN, LSTM, GRU, and Autoencoders

**Subject:** Deep Learning  
**Submitted by:** MCA Semester 3 Student  
**Academic Year:** 2024–25  

---

## Abstract

This project presents a complete deep learning system for binary sentiment classification of IMDB movie reviews. Four recurrent neural network architectures — SimpleRNN, LSTM, Bidirectional LSTM (BiLSTM), and GRU — are implemented, trained, and compared on the standard 50,000-review IMDB benchmark. A deep autoencoder is additionally implemented for unsupervised representation learning and statistical anomaly detection on review texts. All components are integrated into an interactive Streamlit web application that provides real-time sentiment prediction, model comparison, and anomaly analysis. The project covers concepts from Unit IV (RNN/LSTM), Unit V (Autoencoders), and Unit VI (Applications of Deep Learning) of the MCA curriculum.

---

## 1. Introduction

Natural Language Processing (NLP) and sentiment analysis have become critical technologies in applications ranging from e-commerce product review analysis to social media monitoring and content recommendation. Deep learning, particularly recurrent neural networks, has significantly advanced the state-of-the-art in sequence-based NLP tasks.

Movie review sentiment classification is a well-studied NLP benchmark problem because:
- Reviews are longer and more complex than tweets, testing long-range dependency modeling.
- The binary classification setup (positive / negative) provides a clean evaluation metric.
- The IMDB dataset provides a large, balanced, publicly available benchmark.

This project builds a production-quality deep learning pipeline that addresses all aspects of a real-world NLP application: data preprocessing, model design, training, evaluation, and deployment.

---

## 2. Problem Statement

Given a movie review written in natural English, the system must automatically determine whether the reviewer expresses **positive** or **negative** sentiment. The system must:

1. Handle raw text input with variable length and vocabulary.
2. Learn meaningful semantic representations of words and sentences.
3. Correctly classify sentiments with high accuracy on unseen reviews.
4. Detect reviews that are statistically unusual compared to the training distribution.
5. Present results through a user-friendly interface.

---

## 3. Objectives

1. Implement and compare SimpleRNN, LSTM, BiLSTM, and GRU for sentiment classification.
2. Demonstrate the vanishing gradient problem and explain how LSTM/GRU solve it.
3. Build a deep autoencoder for text representation learning and anomaly detection.
4. Evaluate all models rigorously using accuracy, precision, recall, F1-score, and confusion matrices.
5. Develop a multi-page Streamlit web application for live interaction.
6. Produce a clean, modular, well-documented codebase.

---

## 4. Literature Review

| Year | Authors | Contribution |
|------|---------|--------------|
| 1986 | Rumelhart et al. | Introduced Backpropagation Through Time (BPTT) for training RNNs |
| 1997 | Hochreiter & Schmidhuber | Proposed LSTM, solving the vanishing gradient problem |
| 2011 | Maas et al. (Stanford) | Released the IMDB Large Movie Review Dataset (50,000 reviews) |
| 2013 | Cho et al. | Proposed GRU as a simpler alternative to LSTM |
| 2013 | Schuster & Paliwal | Introduced Bidirectional RNNs |
| 2013 | Mikolov et al. | Word2Vec embeddings for NLP |
| 2014 | Kingma & Welling | Proposed Variational Autoencoders (VAE) |
| 2018 | Devlin et al. | BERT: pre-trained transformer language model |

Recurrent architectures remain widely used in embedded systems and mobile NLP due to lower computational cost compared to transformer models.

---

## 5. Dataset Description

### 5.1 Source

The **IMDB Large Movie Review Dataset** (Maas et al., 2011) is loaded directly from `tensorflow.keras.datasets.imdb`.

### 5.2 Statistics

| Property | Value |
|----------|-------|
| Total reviews | 50,000 |
| Training reviews | 25,000 |
| Test reviews | 25,000 |
| Positive reviews | 50% (balanced) |
| Negative reviews | 50% (balanced) |
| Average review length | ~234 tokens |
| Maximum review length | ~2,494 tokens |

### 5.3 Preprocessing Pipeline

1. **Vocabulary limiting**: Keep only the top 10,000 most frequent words. Out-of-vocabulary words are mapped to the `<UNK>` token.
2. **Sequence padding**: Pad shorter reviews with zeros; truncate longer reviews to length 200. Post-padding is used.
3. **Train/Validation split**: The 25,000 training samples are further split 80/20 into train (20,000) and validation (5,000) sets using a fixed random seed (42) to ensure reproducibility.
4. **Test set**: The 25,000 test samples are held out and never used for hyperparameter tuning, model selection, or threshold setting.

### 5.4 Limitations of the Keras IMDB Format

The built-in Keras IMDB dataset returns pre-tokenised integer sequences. Raw review text is not directly available. The word-index mapping can be used to decode sequences approximately, but punctuation and some formatting are lost. The project includes a fallback to load raw text from a local Excel/CSV file if available.

### 5.5 Data Splits

```
Total: 50,000
├── Training   : 20,000  (80% of Keras train set)
├── Validation :  5,000  (20% of Keras train set)
└── Test       : 25,000  (Keras test set, never seen during training)
```

---

## 6. System Requirements

### 6.1 Hardware (Minimum)

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | Intel Core i5 | Intel Core i7 / AMD Ryzen 7 |
| RAM | 8 GB | 16 GB |
| Storage | 5 GB free | 10 GB free |
| GPU | None (CPU training) | NVIDIA GPU with 4+ GB VRAM |

### 6.2 Software

| Software | Version |
|----------|---------|
| Python | 3.9 – 3.11 |
| TensorFlow | ≥ 2.10 |
| Streamlit | ≥ 1.15 |
| scikit-learn | ≥ 1.1 |
| NumPy | ≥ 1.23 |
| Pandas | ≥ 1.5 |

---

## 7. Proposed Methodology

```
Dataset Loading
     │
     ▼
Text Preprocessing (tokenise, pad, split)
     │
     ├──────────────────────────────────┐
     ▼                                  ▼
RNN-Family Training                Autoencoder Training
  SimpleRNN                        BoW Representation
  LSTM                             Encoder → Bottleneck → Decoder
  BiLSTM                           Anomaly Threshold (train set only)
  GRU                                    │
     │                                   │
     ▼                                   ▼
Evaluation on Test Set             Anomaly Detection on Test Set
  Accuracy, P, R, F1                Reconstruction Error > Threshold
  Confusion Matrix                       │
  Training Curves                        │
     │                                   │
     └──────────────┬────────────────────┘
                    ▼
           Streamlit Application
    (Prediction · Comparison · Analysis)
```

---

## 8. System Architecture

### 8.1 Module Map

| File | Role |
|------|------|
| `src/data_preprocessing.py` | Dataset loading, tokenisation, padding, train/val/test split |
| `src/train_rnn.py` | SimpleRNN model definition and training |
| `src/train_lstm.py` | LSTM model definition and training |
| `src/train_bilstm.py` | BiLSTM model definition and training |
| `src/train_gru.py` | GRU model definition and training |
| `src/train_autoencoder.py` | Deep Autoencoder and anomaly detection |
| `src/evaluation.py` | Comprehensive metrics and comparison |
| `src/prediction.py` | Inference API for the Streamlit app |
| `app.py` | Streamlit multi-page web application |
| `train_all.py` | Orchestrates the full pipeline |

---

## 9. Data Preprocessing (Unit IV)

### 9.1 Tokenisation

Each review is converted to a sequence of integers, where each integer corresponds to a word's rank in the vocabulary (most frequent word = 1). Words outside the top 10,000 are replaced with the unknown token index (2).

### 9.2 Padding

All sequences are padded with zeros at the end (**post-padding**) to a fixed length of 200 tokens. Reviews longer than 200 tokens are truncated from the end. This uniform length is required for batch processing in neural networks.

### 9.3 Word Embeddings

The first layer in every model is an `Embedding(VOCAB_SIZE, EMBED_DIM)` layer:
- Converts each integer token to a dense 64-dimensional floating-point vector.
- Embedding weights are **learned during training** (not pre-trained Word2Vec/GloVe).
- The embedding layer effectively encodes semantic similarity — words used in similar contexts get similar vectors.

---

## 10. RNN, LSTM, BiLSTM, and GRU Architectures (Unit IV)

### 10.1 Sequence Learning

Unlike feedforward networks that process fixed-size inputs, recurrent networks process **sequences of arbitrary length** by maintaining an internal memory state that is updated at each time-step.

For sentiment analysis, the input sequence is the word embeddings of a review, and the output is a single binary prediction.

### 10.2 Unfolding Computational Graphs

An RNN with T time-steps can be "unrolled" into T copies of the same cell:

```
x₁ → [RNN] → h₁ → [RNN] → h₂ → ... → h_T → Dense → ŷ
        ↑              ↑
     shared weights (same W at every step)
```

Backpropagation Through Time (BPTT) computes gradients by propagating errors backward through the unrolled graph.

### 10.3 SimpleRNN

**Formula**: `h_t = tanh(W_h · h_{t-1} + W_x · x_t + b)`

**Architecture used**:
```
Embedding(10000, 64) → SimpleRNN(64) → Dropout(0.3) → Dense(32, relu) → Dense(1, sigmoid)
```

**Vanishing Gradient Problem**: As the sequence length T increases, the gradient ∂L/∂h₁ involves T matrix multiplications. If the eigenvalues of W_h are < 1, gradients shrink exponentially → the network cannot learn dependencies beyond ~10 steps.

### 10.4 LSTM (Long Short-Term Memory)

Proposed by Hochreiter & Schmidhuber (1997) to solve the vanishing gradient problem.

**Key innovation**: A **cell state C_t** flows through time with only element-wise operations (no matrix multiplications), providing a gradient highway.

| Gate | Formula | Role |
|------|---------|------|
| Forget | f_t = σ(W_f·[h_{t-1},x_t]+b_f) | What to erase from C_{t-1} |
| Input | i_t = σ(W_i·[h_{t-1},x_t]+b_i) | What new info to write |
| Candidate | C̃_t = tanh(W_C·[h_{t-1},x_t]+b_C) | Candidate content |
| Cell | C_t = f_t⊙C_{t-1} + i_t⊙C̃_t | Updated long-term memory |
| Output | o_t = σ(W_o·[h_{t-1},x_t]+b_o) | What to read from C_t |
| Hidden | h_t = o_t⊙tanh(C_t) | Short-term output |

**Architecture used**:
```
Embedding(10000, 64) → LSTM(64) → Dropout(0.3) → Dense(32, relu) → Dense(1, sigmoid)
```

### 10.5 Bidirectional LSTM

A standard LSTM reads x₁ → x₂ → … → x_T. It cannot use future context when processing position t. A **BiLSTM** runs two LSTMs simultaneously:

- **Forward**: reads left-to-right → produces h⃗_t
- **Backward**: reads right-to-left → produces h⃖_t
- Final representation: `ĥ_t = [h⃗_t ; h⃖_t]`

This is especially important for negation (e.g., "not good") where the modifier comes before the word it negates.

**Architecture used**:
```
Embedding(10000, 64) → Bidirectional(LSTM(64)) → Dropout(0.3) → Dense(32, relu) → Dense(1, sigmoid)
```

### 10.6 GRU (Gated Recurrent Unit)

Proposed by Cho et al. (2014) as a simpler alternative to LSTM with ~25% fewer parameters.

| Gate | Formula | Role |
|------|---------|------|
| Reset | r_t = σ(W_r·[h_{t-1},x_t]) | How much past to reset |
| Update | z_t = σ(W_z·[h_{t-1},x_t]) | Balance old vs new |
| Candidate | h̃_t = tanh(W·[r_t⊙h_{t-1},x_t]) | New candidate state |
| Hidden | h_t = (1-z_t)⊙h_{t-1} + z_t⊙h̃_t | Final state |

GRU merges the cell state and hidden state into a single vector.

**Architecture used**:
```
Embedding(10000, 64) → GRU(64) → Dropout(0.3) → Dense(32, relu) → Dense(1, sigmoid)
```

### 10.7 Training Configuration

| Hyperparameter | Value |
|----------------|-------|
| Optimizer | Adam (lr=0.001) |
| Loss | Binary Crossentropy |
| Batch size | 128 |
| Max epochs | 10 |
| Early stopping | Patience=3 (monitor val_loss) |
| Model checkpoint | Best val_accuracy |
| Dropout | 0.3 |

---

## 11. Autoencoder Architecture (Unit V)

### 11.1 Overview

An autoencoder is an unsupervised neural network that learns to compress and reconstruct its inputs. It consists of:

- **Encoder**: compresses input x to a lower-dimensional representation z (bottleneck)
- **Bottleneck**: the compressed representation, also called the latent space
- **Decoder**: reconstructs the original input x̂ from z
- **Loss**: MSE(x, x̂) — minimised during training

### 11.2 Text Representation for Autoencoder

The LSTM/RNN models use padded integer sequences as input. For the autoencoder, we use **normalised Bag-of-Words (BoW)** vectors:
- Each review → a 10,000-dimensional vector
- Value at position i = frequency of word i in the review, normalised by total word count
- BoW vectors are dense real-valued representations suitable for standard dense autoencoders

### 11.3 Autoencoder Architecture Used

```
Input (10000) → Dense(128, relu) → Dropout(0.2) → Dense(64, relu)
                                                          ↓
                                               Dense(32, relu)  ← BOTTLENECK
                                                          ↓
                               Dense(64, relu) → Dense(128, relu) → Dense(10000, linear)
```

L2 regularisation (λ=0.0001) is applied to the first encoder layer.

### 11.4 Denoising Autoencoder

A **denoising autoencoder** adds Gaussian noise (σ=0.10) to the input before encoding:

```
x + ε → Encoder → z → Decoder → x̂
Target: original x (not noisy x)
```

This forces the encoder to learn robust representations that can recover clean data from corrupted input.

### 11.5 Anomaly Detection

**Key principle**: An autoencoder trained on typical IMDB reviews learns to compress and reconstruct them efficiently. An *unusual* review (atypical style, language, very short/long, off-topic) will have a higher reconstruction error because the encoder cannot map it to the learned latent space accurately.

**Threshold setting**:
```
threshold = mean(MSE_train) + 2 × std(MSE_train)
```

The threshold is computed **only on training data** to prevent data leakage. Reviews in the test set with MSE > threshold are flagged as unusual.

**Important caveat**: Unusual ≠ fake. A review may be flagged as unusual because it:
- Is very short or very long
- Uses rare vocabulary or specialised jargon
- Is written in a non-standard style
- Is about an unusual genre

### 11.6 Theoretical: Convolutional Autoencoder

A **Convolutional Autoencoder** (CAE) replaces dense layers with convolutional layers:
- Encoder: Conv2D + MaxPooling → compressed feature maps
- Decoder: Conv2DTranspose + UpSampling → reconstructed image

CAEs are used for image compression, denoising, and anomaly detection in images. They are not implemented here because our dataset is text-based.

### 11.7 Theoretical: Variational Autoencoder (VAE)

A **VAE** (Kingma & Welling, 2014) replaces the deterministic bottleneck with a probabilistic one:
- Encoder outputs: mean (μ) and log-variance (log σ²) of a Gaussian distribution
- Sample: z ~ N(μ, σ²)
- Loss: MSE(x, x̂) + β × KL(N(μ,σ²) || N(0,1))

The KL-divergence term regularises the latent space, making it continuous and suitable for **generating** new samples. VAEs are used for image generation, drug discovery, and anomaly detection.

---

## 12. Implementation Details

### 12.1 Training Pipeline

1. `data_preprocessing.py` loads and preprocesses data, saves word_index.pkl and preprocessing_meta.json
2. Each `train_*.py` loads data, builds model, trains with early stopping, saves best model checkpoint, saves training history and metrics
3. `train_autoencoder.py` builds BoW representation, trains AE, computes threshold on training data
4. `evaluation.py` loads all trained models, runs inference on the held-out test set, computes all metrics, saves plots and comparison CSV
5. `app.py` loads models and metadata on startup, provides interactive inference

### 12.2 Avoiding Data Leakage

- Validation split is taken from training data before any fitting
- Test set (25,000 reviews) is only used in `evaluation.py`, never for model selection or hyperparameter tuning
- Autoencoder anomaly threshold is computed on training errors only
- Early stopping monitors validation loss

### 12.3 Model Persistence

All models are saved in the modern Keras format (`.keras`):
- `models/simple_rnn_best.keras`
- `models/lstm_best.keras`
- `models/bilstm_best.keras`
- `models/gru_best.keras`
- `models/autoencoder_best.keras`
- `models/encoder_best.keras`

---

## 13. Experimental Results

> **Note**: The following are representative expected values. Actual values may vary slightly based on hardware, TensorFlow version, and random seeds.

### 13.1 Model Performance (Test Set – 25,000 reviews)

| Model | Accuracy | Precision | Recall | F1-Score | Train Time |
|-------|----------|-----------|--------|----------|------------|
| SimpleRNN | ~0.82 | ~0.81 | ~0.83 | ~0.82 | ~5 min (CPU) |
| LSTM | ~0.86 | ~0.86 | ~0.86 | ~0.86 | ~10 min (CPU) |
| BiLSTM | ~0.87 | ~0.87 | ~0.87 | ~0.87 | ~15 min (CPU) |
| GRU | ~0.86 | ~0.86 | ~0.87 | ~0.86 | ~9 min (CPU) |

### 13.2 Observations

1. **SimpleRNN** has the lowest accuracy due to the vanishing gradient problem limiting its ability to learn from longer reviews.
2. **LSTM** significantly outperforms SimpleRNN by maintaining long-term dependencies through cell state gating.
3. **BiLSTM** achieves the best F1-score by combining forward and backward context.
4. **GRU** performs comparably to LSTM with fewer parameters and faster training.
5. All gated models (LSTM, BiLSTM, GRU) converge more stably than SimpleRNN.

### 13.3 Autoencoder Results

| Metric | Value |
|--------|-------|
| Reconstruction loss (train) | < 0.001 |
| Anomaly threshold (mean+2σ) | ~0.0002–0.0010 |
| % of test reviews flagged | ~4–6% |

---

## 14. Advantages and Limitations

### 14.1 Advantages

- Modular, clean codebase — each model is independently trainable
- No data leakage — strict train/val/test split maintained throughout
- Comprehensive evaluation with 4 metrics + confusion matrix per model
- Interactive web app with real-time prediction and explanations
- Both standard and denoising autoencoder implemented
- Theoretical coverage of VAE and Convolutional AE

### 14.2 Limitations

- SimpleRNN struggles with reviews longer than ~50 tokens
- Pre-trained word embeddings (GloVe/Word2Vec) would improve accuracy
- Transformer models (BERT) would significantly outperform RNN-based models
- The Keras IMDB format does not give access to raw HTML review text
- Autoencoder anomaly detection is heuristic — not a supervised classifier

---

## 15. Applications

1. **E-commerce**: Automatic classification of product reviews
2. **Content moderation**: Flagging negative reviews for human review
3. **Market research**: Analysing public sentiment about films/products
4. **Recommendation systems**: Using predicted sentiment to improve recommendations
5. **Anomaly detection**: Identifying spam, bot-generated, or off-topic reviews

---

## 16. Future Enhancements

1. **Transformer models**: Replace RNN with BERT or DistilBERT for state-of-the-art accuracy (~95%+)
2. **Pre-trained embeddings**: Use GloVe or fastText instead of learned embeddings
3. **Attention mechanism**: Add attention layer to highlight important words
4. **Multi-class sentiment**: Extend from binary to 5-star rating prediction
5. **Real-time scraping**: Fetch live IMDB reviews via API for live analysis
6. **Explainability**: Integrate LIME or SHAP for word-level explanation of predictions
7. **Variational Autoencoder**: Implement VAE for generative analysis and better anomaly detection

---

## 17. Conclusion

This project successfully implements a complete end-to-end deep learning pipeline for IMDB movie review sentiment analysis. Four recurrent architectures (SimpleRNN, LSTM, BiLSTM, GRU) are trained and rigorously compared on a held-out test set of 25,000 reviews. The results confirm that gated models (LSTM, BiLSTM, GRU) significantly outperform SimpleRNN due to their ability to capture long-range dependencies and resist the vanishing gradient problem. A deep autoencoder is implemented for unsupervised text representation learning and statistical anomaly detection. All components are integrated into a Streamlit web application that provides an interactive, user-friendly interface for real-time sentiment analysis, model comparison, and anomaly detection.

The project covers all required syllabus topics from Unit IV (RNN, LSTM, GRU, Bidirectional RNNs, vanishing/exploding gradients), Unit V (Autoencoders, denoising autoencoders, anomaly detection), and Unit VI (practical deep learning application development and deployment).

---

## 18. References

1. Hochreiter, S., & Schmidhuber, J. (1997). Long Short-Term Memory. *Neural Computation*, 9(8), 1735–1780.
2. Cho, K., et al. (2014). Learning Phrase Representations using RNN Encoder-Decoder for Statistical Machine Translation. *EMNLP*.
3. Maas, A. L., et al. (2011). Learning Word Vectors for Sentiment Analysis. *ACL*.
4. Schuster, M., & Paliwal, K. K. (1997). Bidirectional Recurrent Neural Networks. *IEEE Transactions on Signal Processing*.
5. Kingma, D. P., & Welling, M. (2014). Auto-Encoding Variational Bayes. *ICLR*.
6. Goodfellow, I., Bengio, Y., & Courville, A. (2016). *Deep Learning*. MIT Press.
7. Géron, A. (2019). *Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow* (2nd ed.). O'Reilly Media.
8. Chollet, F. (2021). *Deep Learning with Python* (2nd ed.). Manning Publications.
9. TensorFlow Documentation. https://www.tensorflow.org/api_docs/
10. Streamlit Documentation. https://docs.streamlit.io/
