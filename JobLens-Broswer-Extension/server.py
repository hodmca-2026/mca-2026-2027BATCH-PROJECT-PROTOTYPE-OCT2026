"""Flask API. The extension sends the page HTML; we parse it (crawler.py) and score it."""
import pickle
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from tensorflow import keras

from crawler import html_to_text

app = Flask(__name__)
CORS(app)

model = keras.models.load_model("autoencoder.keras")
meta = pickle.load(open("meta.pkl", "rb"))
vec, threshold = meta["vectorizer"], meta["threshold"]


@app.route("/predict", methods=["POST"])
def predict():
    html = request.get_json().get("html", "")
    title, text = html_to_text(html)
    x = vec.transform([title + " " + text]).toarray().astype("float32")
    error = float(np.mean((x - model.predict(x, verbose=0)) ** 2))
    return jsonify({
        "error": error,
        "threshold": threshold,
        "fraud": bool(error > threshold),
    })


if __name__ == "__main__":
    app.run(port=5000)
