"""
app.py
======
Streamlit Web Application – IMDB Sentiment Analysis Dashboard

Features:
  A. Sentiment Prediction (single model or all models)
  B. Model Comparison Dashboard
  C. Autoencoder Anomaly Detection
  D. Evaluation Dashboard (training curves, confusion matrices)

Run:
    streamlit run app.py
"""

import os, sys, json, time
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

# ── Path setup ─────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

EVAL_DIR   = os.path.join(BASE_DIR, "evaluation_results")
MODELS_DIR = os.path.join(BASE_DIR, "models")
DATA_DIR   = os.path.join(BASE_DIR, "data")

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IMDB Sentiment Analyzer",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

MODEL_DISPLAY = {
    "simple_rnn": "SimpleRNN",
    "lstm":       "LSTM",
    "bilstm":     "BiLSTM",
    "gru":        "GRU",
}
ALL_MODELS = list(MODEL_DISPLAY.keys())


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner="Loading model …")
def get_predictor():
    """Load prediction module (caches across reruns)."""
    try:
        from src.prediction import (
            predict_sentiment, predict_all_models,
            compute_reconstruction_error,
            get_model_metrics, get_best_model_name,
        )
        return {
            "predict":     predict_sentiment,
            "predict_all": predict_all_models,
            "ae":          compute_reconstruction_error,
            "metrics":     get_model_metrics,
            "best":        get_best_model_name,
        }
    except Exception as e:
        return {"error": str(e)}


def models_available():
    """Return list of model names that have been trained."""
    return [
        n for n in ALL_MODELS
        if os.path.exists(os.path.join(MODELS_DIR, f"{n}_best.keras"))
    ]


def load_json_safe(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def load_image_safe(path):
    from PIL import Image
    if os.path.exists(path):
        return Image.open(path)
    return None


def sentiment_colour(label: str):
    return "🟢" if label == "Positive" else "🔴"


# ──────────────────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────────────────

def sidebar():
    logo_path = os.path.join(BASE_DIR, "assets", "imdb_logo.png")
    if os.path.exists(logo_path):
        st.sidebar.image(logo_path, width=160)
    else:
        st.sidebar.markdown("## 🎬 IMDb")
    st.sidebar.title("🎬 Sentiment Analyzer")
    st.sidebar.markdown("**Deep Learning | MCA Project**")
    st.sidebar.markdown("---")
    page = st.sidebar.radio(
        "Navigate",
        [
            "🏠 Home",
            "🔮 Sentiment Prediction",
            "📊 Model Comparison",
            "🔍 Autoencoder Analysis",
            "📈 Evaluation Dashboard",
            "📚 Theory & Architecture",
        ],
        index=0,
    )
    st.sidebar.markdown("---")
    avail = models_available()
    st.sidebar.markdown(f"**Trained models:** {len(avail)}/{len(ALL_MODELS)}")
    for n in ALL_MODELS:
        icon = "✅" if n in avail else "❌"
        st.sidebar.markdown(f"{icon} {MODEL_DISPLAY[n]}")
    ae_trained = os.path.exists(os.path.join(MODELS_DIR, "autoencoder_best.keras"))
    st.sidebar.markdown(f"{'✅' if ae_trained else '❌'} Autoencoder")
    return page


# ──────────────────────────────────────────────────────────────────────────────
# PAGE: Home
# ──────────────────────────────────────────────────────────────────────────────

def page_home():
    st.title("🎬 Deep Learning-Based IMDB Movie Review Sentiment Analysis")
    st.markdown(
        """
        Welcome to the **MCA Deep Learning Project** dashboard.

        This application demonstrates:
        | Module | Technique |
        |--------|-----------|
        | **Sequence Classification** | SimpleRNN, LSTM, BiLSTM, GRU for sentiment analysis |
        | **Representation Learning** | Deep Autoencoder for anomaly detection |
        | **Deployment** | End-to-end NLP application deployed with Streamlit |

        ### Dataset
        - **IMDB Movie Reviews** – 50,000 reviews (40k train / 10k test)
        - Binary classification: **Positive (1)** or **Negative (0)**
        - Preprocessed via tokenisation, vocabulary limiting (top 10,000 words), and padding to length 200

        ### Quick Start
        ```bash
        # 1. Install dependencies
        pip install -r requirements.txt

        # 2. Train all models (run once)
        python train_all.py

        # 3. Launch the app
        streamlit run app.py
        ```
        """
    )
    avail = models_available()
    if not avail:
        st.warning(
            "⚠️ No trained models found. Run **`python train_all.py`** first, then refresh this page."
        )
    else:
        st.success(f"✅ {len(avail)} model(s) ready. Navigate using the sidebar.")

    col1, col2, col3 = st.columns(3)
    col1.metric("Training samples", "35,000")
    col2.metric("Validation samples", "5,000")
    col3.metric("Test samples", "10,000")


# ──────────────────────────────────────────────────────────────────────────────
# PAGE: Sentiment Prediction
# ──────────────────────────────────────────────────────────────────────────────

def page_prediction(pred):
    st.title("🔮 Sentiment Prediction")
    st.markdown(
        "Enter a movie review below and the selected model will predict whether "
        "it expresses **positive** or **negative** sentiment."
    )

    avail = models_available()
    if not avail:
        st.error("No trained models found. Run `python train_all.py` first.")
        return

    col_a, col_b = st.columns([3, 1])
    with col_a:
        review_text = st.text_area(
            "📝 Enter your movie review:",
            height=160,
            placeholder="e.g. 'This film was absolutely brilliant …'",
        )
    with col_b:
        selected_model = st.selectbox(
            "Choose model",
            [MODEL_DISPLAY[n] for n in avail],
        )
        run_all = st.checkbox("Compare all models", value=False)
        predict_btn = st.button("🎯 Predict", use_container_width=True)

    # ── Validation ─────────────────────────────────────────────────────────────
    if predict_btn:
        if not review_text or not review_text.strip():
            st.warning("Please enter a review before predicting.")
            return
        if len(review_text.split()) < 3:
            st.info("ℹ️ Very short input. Results may be less reliable.")

        model_key = {v: k for k, v in MODEL_DISPLAY.items()}[selected_model]

        if run_all:
            st.subheader("Results across all models")
            rows = pred["predict_all"](review_text)
            for r in rows:
                if r["label"] == "Not trained":
                    continue
                icon = sentiment_colour(r["label"])
                c1, c2, c3, c4 = st.columns(4)
                c1.markdown(f"**{r['model']}**")
                c2.markdown(f"{icon} {r['label']}")
                c3.progress(r["probability"] if r["label"] == "Positive" else 1-r["probability"])
                c4.markdown(f"`{r['confidence']*100:.1f}%` confidence")
        else:
            with st.spinner("Running inference …"):
                result = pred["predict"](review_text, model_name=model_key)

            icon = sentiment_colour(result["label"])
            st.markdown("---")
            st.subheader(f"Prediction: {icon} {result['label']}")

            prob = result["probability"]
            bar_val = prob if result["label"] == "Positive" else 1 - prob

            col1, col2, col3 = st.columns(3)
            col1.metric("Sentiment", result["label"])
            col2.metric("Confidence", f"{result['confidence']*100:.1f}%")
            col3.metric("Inference", f"{result['infer_ms']:.1f} ms")

            st.markdown("**Probability score (P(Positive))**")
            st.progress(float(prob))
            st.caption(
                f"P(positive) = **{prob:.4f}** | P(negative) = **{1-prob:.4f}**\n\n"
                "A score > 0.5 indicates positive sentiment. "
                "The further from 0.5, the more confident the model."
            )

            if len(review_text.split()) > 400:
                st.info(
                    "ℹ️ Your review is longer than 400 words. The model truncates input "
                    "to 200 tokens – some information at the end may be ignored."
                )


# ──────────────────────────────────────────────────────────────────────────────
# PAGE: Model Comparison
# ──────────────────────────────────────────────────────────────────────────────

def page_comparison():
    st.title("📊 Model Comparison")
    st.markdown(
        "Performance of **SimpleRNN**, **LSTM**, **BiLSTM**, and **GRU** on the "
        "held-out IMDB test set (25,000 reviews)."
    )

    csv_path = os.path.join(EVAL_DIR, "model_comparison.csv")
    if not os.path.exists(csv_path):
        st.warning("Run `python src/evaluation.py` to generate comparison results.")
        return

    df = pd.read_csv(csv_path)

    # ── Table ──────────────────────────────────────────────────────────────────
    st.subheader("Summary Table")
    fmt_cols = ["Accuracy", "Precision", "Recall", "F1-Score"]
    styled = df.style.format({c: "{:.4f}" for c in fmt_cols if c in df.columns}) \
                     .highlight_max(subset=fmt_cols, color="#c8f7c5")
    st.dataframe(styled, use_container_width=True)

    # ── Bar chart ──────────────────────────────────────────────────────────────
    chart_path = os.path.join(EVAL_DIR, "model_comparison_chart.png")
    img = load_image_safe(chart_path)
    if img:
        st.image(img, caption="Model Comparison – Accuracy / Precision / Recall / F1", use_column_width=True)

    # ── Training curves ────────────────────────────────────────────────────────
    st.subheader("Training & Validation Curves")
    avail = models_available()
    tabs  = st.tabs([MODEL_DISPLAY[n] for n in avail])
    for tab, name in zip(tabs, avail):
        with tab:
            path = os.path.join(EVAL_DIR, f"{name}_training_curves.png")
            img  = load_image_safe(path)
            if img:
                st.image(img, use_column_width=True)
            else:
                st.info(f"Training curve not found for {MODEL_DISPLAY[name]}.")

    # ── Architecture comparison ────────────────────────────────────────────────
    st.subheader("Architecture Summary")
    st.markdown(
        """
        | Model | Gates | Parameters (approx.) | Key Strength | Key Weakness |
        |-------|-------|-----------------------|--------------|--------------|
        | **SimpleRNN** | None | ~700K | Fast training | Vanishing gradient |
        | **LSTM** | 3 (forget, input, output) | ~880K | Long-range dependencies | More parameters |
        | **BiLSTM** | 3 × 2 directions | ~1.1M | Full context (left+right) | Slowest training |
        | **GRU** | 2 (update, reset) | ~820K | Efficient, near-LSTM accuracy | Slightly less capacity |
        """
    )


# ──────────────────────────────────────────────────────────────────────────────
# PAGE: Autoencoder Analysis
# ──────────────────────────────────────────────────────────────────────────────

def page_autoencoder(pred):
    st.title("🔍 Autoencoder Anomaly Detection")
    st.markdown(
        """
        The **Deep Autoencoder** (Unit V) learns to compress and reconstruct
        typical IMDB reviews. A review with an unusually **high reconstruction
        error** is flagged as statistically atypical.

        > ⚠️ **Important**: High reconstruction error means the review is
        > different from the training distribution.  It does **NOT** mean the
        > review is fake, spam, or malicious.

        ### How it works
        1. **Encoder**: compresses the review's BoW vector into a 32-dimensional bottleneck.
        2. **Decoder**: reconstructs the original vector from the bottleneck.
        3. **MSE** between original and reconstructed vector = **reconstruction error**.
        4. Threshold = mean + 2×std of training-set errors (set using training data only).
        """
    )

    ae_path = os.path.join(MODELS_DIR, "autoencoder_best.keras")
    if not os.path.exists(ae_path):
        st.error("Autoencoder not trained. Run `python train_all.py` first.")
        return

    review_text = st.text_area(
        "📝 Enter a review to analyse:",
        height=140,
        placeholder="e.g. 'This film changed my life …'",
    )

    if st.button("🔍 Analyse", use_container_width=False):
        if not review_text.strip():
            st.warning("Please enter a review.")
            return

        with st.spinner("Computing reconstruction error …"):
            result = pred["ae"](review_text)

        if result.get("error") is None:
            st.error(result["note"])
            return

        col1, col2, col3 = st.columns(3)
        col1.metric("Reconstruction Error (MSE)", f"{result['error']:.6f}")
        col2.metric("Anomaly Threshold", f"{result['threshold']:.6f}")
        flag = result["flagged"]
        col3.metric("Status", "⚠️ Unusual" if flag else "✅ Normal")

        if flag:
            st.warning(result["note"])
        else:
            st.success(result["note"])

        # Visual gauge
        ratio = min(result["error"] / (result["threshold"] * 2), 1.0)
        st.markdown("**Error vs Threshold (normalised)**")
        st.progress(float(ratio))
        st.caption(f"Bar full = 2× threshold. Red zone = flagged.")

    # ── Error distribution plots ───────────────────────────────────────────────
    st.subheader("Reconstruction Error Distribution")
    err_plot = os.path.join(EVAL_DIR, "autoencoder_reconstruction_errors.png")
    img = load_image_safe(err_plot)
    if img:
        st.image(img, caption="Distribution of reconstruction errors on Train and Test sets", use_column_width=True)

    loss_plot = os.path.join(EVAL_DIR, "autoencoder_training_loss.png")
    img2 = load_image_safe(loss_plot)
    if img2:
        st.image(img2, caption="Autoencoder Training Loss (MSE)", use_column_width=True)

    # ── Theory ────────────────────────────────────────────────────────────────
    with st.expander("📖 Autoencoder Theory (Unit V)"):
        st.markdown(
            """
            ### Standard Autoencoder
            An autoencoder is an unsupervised neural network with a symmetric
            encoder–decoder structure:

            ```
            INPUT x  →  Encoder  →  Bottleneck z  →  Decoder  →  Output x̂
            ```

            The loss function minimises **reconstruction error**:

                L = MSE(x, x̂) = (1/n) Σ (xᵢ - x̂ᵢ)²

            The bottleneck forces the network to learn a **compressed
            representation** that captures the most important features.

            ### Denoising Autoencoder
            Adds Gaussian noise to inputs during training:

                x_noisy = x + ε,  ε ~ N(0, σ²)
                Target  = clean x

            This regularises the encoder, making it robust to noise.

            ### Convolutional Autoencoder (Theory)
            Replaces dense layers with Conv2D/Conv2DTranspose layers.
            Used for **image compression** and **anomaly detection in images**.
            Not implemented here because our dataset is text-based.

            ### Variational Autoencoder (Theory)
            The VAE encoder outputs a **distribution** (μ, σ) rather than
            a point estimate. It samples z ~ N(μ, σ²) and adds a KL-divergence
            penalty to regularise the latent space, enabling **generation**
            of new samples.
            """
        )


# ──────────────────────────────────────────────────────────────────────────────
# PAGE: Evaluation Dashboard
# ──────────────────────────────────────────────────────────────────────────────

def page_evaluation():
    st.title("📈 Evaluation Dashboard")
    st.markdown("Detailed evaluation results for all trained models.")

    avail = models_available()
    if not avail:
        st.error("No trained models found.")
        return

    selected = st.selectbox("Select model", [MODEL_DISPLAY[n] for n in avail])
    name_key = {v: k for k, v in MODEL_DISPLAY.items()}[selected]

    metrics = load_json_safe(os.path.join(EVAL_DIR, f"{name_key}_metrics.json"))

    if metrics:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Test Accuracy",  f"{metrics.get('test_accuracy', metrics.get('test_acc', 0)):.4f}")
        c2.metric("Precision",      f"{metrics.get('test_precision', 0):.4f}")
        c3.metric("Recall",         f"{metrics.get('test_recall', 0):.4f}")
        c4.metric("F1-Score",       f"{metrics.get('test_f1', 0):.4f}")

        c5, c6 = st.columns(2)
        c5.metric("Train Time", f"{metrics.get('train_time', 0):.1f} s")
        c6.metric("Epochs run", metrics.get("epochs_run", "—"))
    else:
        st.info("Run `python src/evaluation.py` to compute detailed metrics.")

    # ── Training curves ─────────────────────────────────────────────────────
    st.subheader("Training Curves")
    curve_img = load_image_safe(os.path.join(EVAL_DIR, f"{name_key}_training_curves.png"))
    if curve_img:
        st.image(curve_img, use_column_width=True)

    # ── Confusion matrix ────────────────────────────────────────────────────
    st.subheader("Confusion Matrix")
    cm_img = load_image_safe(os.path.join(EVAL_DIR, f"{name_key}_confusion_matrix.png"))
    if cm_img:
        st.image(cm_img, width=450)

    # ── Best model ──────────────────────────────────────────────────────────
    best_info = load_json_safe(os.path.join(EVAL_DIR, "best_model.json"))
    if best_info:
        st.success(
            f"🏆 **Best model**: {best_info.get('best_model', '—')} "
            f"(F1 = {best_info.get('best_f1', 0):.4f})"
        )

    # ── Per-epoch history chart ──────────────────────────────────────────────
    hist = metrics.get("history", {})
    if hist and "accuracy" in hist:
        st.subheader("Epoch-by-Epoch History")
        fig, axes = plt.subplots(1, 2, figsize=(12, 3))
        axes[0].plot(hist["accuracy"],     label="Train")
        axes[0].plot(hist["val_accuracy"], label="Validation")
        axes[0].set_title("Accuracy"); axes[0].legend(); axes[0].grid(alpha=0.3)

        axes[1].plot(hist["loss"],     label="Train")
        axes[1].plot(hist["val_loss"], label="Validation")
        axes[1].set_title("Loss"); axes[1].legend(); axes[1].grid(alpha=0.3)

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()



# ──────────────────────────────────────────────────────────────────────────────
# PAGE: Theory & Architecture
# ──────────────────────────────────────────────────────────────────────────────

def page_theory():
    st.title("📚 Theory & Architecture")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "RNN Basics", "LSTM", "GRU", "Bidirectional RNN", "Autoencoder"
    ])

    with tab1:
        st.markdown(
            """
            ## Recurrent Neural Networks (Unit IV)

            A standard feedforward network maps a fixed-size input to an output.
            A **Recurrent Neural Network (RNN)** processes **sequences** by
            maintaining a **hidden state** h_t that is updated at each time-step:

                h_t = tanh(W_h · h_{t-1} + W_x · x_t + b)

            ### Unfolding Computational Graphs
            An RNN is "unrolled" through time: one copy of the recurrent cell
            for each time-step.  Backpropagation Through Time (BPTT) computes
            gradients by propagating errors backward through all copies.

            ### Vanishing & Exploding Gradients
            During BPTT, gradients are multiplied by the weight matrix at each
            step.  If the largest eigenvalue of W_h is < 1, gradients **vanish**
            exponentially → the network cannot learn long-range dependencies.
            If > 1, gradients **explode** → training becomes unstable.

            **Solutions**: Gradient clipping (for exploding), LSTM / GRU
            (for vanishing via gated connections).
            """
        )

    with tab2:
        st.markdown(
            """
            ## Long Short-Term Memory – LSTM (Hochreiter & Schmidhuber, 1997)

            An LSTM cell adds a **cell state** C_t (long-term memory) alongside
            the hidden state h_t (short-term memory) and controls them with
            three learned gates:

            | Gate | Formula | Role |
            |------|---------|------|
            | **Forget** | f_t = σ(W_f·[h_{t-1},x_t]+b_f) | What to erase from C_{t-1} |
            | **Input** | i_t = σ(W_i·[h_{t-1},x_t]+b_i) | What new info to write |
            | **Candidate** | C̃_t = tanh(W_C·[h_{t-1},x_t]+b_C) | Candidate content to write |
            | **Cell update** | C_t = f_t⊙C_{t-1} + i_t⊙C̃_t | Updated cell state |
            | **Output** | o_t = σ(W_o·[h_{t-1},x_t]+b_o) | What to output |
            | **Hidden** | h_t = o_t⊙tanh(C_t) | Short-term output |

            The cell state flows through time with **only element-wise operations**,
            providing a gradient highway that prevents vanishing gradients.
            """
        )

    with tab3:
        st.markdown(
            """
            ## Gated Recurrent Unit – GRU (Cho et al., 2014)

            A GRU simplifies LSTM by merging cell state and hidden state,
            using only **two gates**:

            | Gate | Formula | Role |
            |------|---------|------|
            | **Reset** | r_t = σ(W_r·[h_{t-1},x_t]) | How much past state to reset |
            | **Update** | z_t = σ(W_z·[h_{t-1},x_t]) | Balance old vs new state |
            | **Candidate** | h̃_t = tanh(W·[r_t⊙h_{t-1},x_t]) | Proposed new state |
            | **Hidden** | h_t = (1-z_t)⊙h_{t-1} + z_t⊙h̃_t | Final state |

            **Advantages over LSTM**: fewer parameters (~25% less), faster
            training, competitive performance on many sequence tasks.
            """
        )

    with tab4:
        st.markdown(
            """
            ## Bidirectional RNN

            A standard RNN reads left-to-right: each h_t sees only past context.
            A **Bidirectional RNN** runs two RNNs simultaneously:

            - **Forward RNN**: x_1 → x_2 → … → x_T  produces  h⃗_t
            - **Backward RNN**: x_T → x_{T-1} → … → x_1  produces  h⃖_t

            The final representation for each position t is:

                ĥ_t = [h⃗_t ; h⃖_t]   (concatenation)

            This gives the model access to **full left and right context**.

            ### Why it helps for sentiment analysis
            Negation words like *"not"* or *"hardly"* modify words that come
            AFTER them.  A forward-only model may miss this.  A BiLSTM can
            connect *"not"* to *"good"* even when separated by many words.
            """
        )

    with tab5:
        st.markdown(
            """
            ## Autoencoders (Unit V)

            ### Structure
            ```
            Input x  ──►  Encoder  ──►  Bottleneck z  ──►  Decoder  ──►  Output x̂
            ```

            - **Encoder**: reduces dimensionality
            - **Bottleneck**: compact latent representation (information bottleneck)
            - **Decoder**: reconstructs original input
            - **Loss**: MSE(x, x̂) – minimised during training

            ### Types
            | Type | Key Feature |
            |------|-------------|
            | **Standard** | Dense layers, MSE loss |
            | **Denoising** | Noisy input → clean reconstruction |
            | **Convolutional** | Conv layers for spatial data (images) |
            | **Variational (VAE)** | Probabilistic bottleneck, KL divergence |

            ### Anomaly Detection
            An autoencoder trained on *normal* data will have **high reconstruction
            error** on *unusual* inputs, because the encoder cannot compress them
            into the learned latent space efficiently.

            Threshold: μ_train + 2σ_train (set on training data only – no data leakage)
            """
        )


# ──────────────────────────────────────────────────────────────────────────────
# Main router
# ──────────────────────────────────────────────────────────────────────────────

def main():
    pred = get_predictor()

    page = sidebar()

    if page == "🏠 Home":
        page_home()
    elif page == "🔮 Sentiment Prediction":
        if "error" in pred:
            st.error(f"Could not load prediction module: {pred['error']}")
        else:
            page_prediction(pred)
    elif page == "📊 Model Comparison":
        page_comparison()
    elif page == "🔍 Autoencoder Analysis":
        if "error" in pred:
            st.error(f"Could not load prediction module: {pred['error']}")
        else:
            page_autoencoder(pred)
    elif page == "📈 Evaluation Dashboard":
        page_evaluation()
    elif page == "📚 Theory & Architecture":
        page_theory()


if __name__ == "__main__":
    main()
