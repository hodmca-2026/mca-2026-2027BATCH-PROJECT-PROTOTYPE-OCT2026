"""
Benchmark Evaluation for Project Similarity Detection
=====================================================
Contains two separate datasets:
1. DEV_SET: Used for threshold calibration and parameter selection.
2. HELD_OUT_TEST_SET: Strictly held out for measuring baseline vs improved
   Precision, Recall, and F1 score.

Covers:
- Positive exact duplicates
- Positive paraphrased duplicates (different wording, same core project)
- Negative hard pairs (shared buzzwords/domain templates e.g. "using deep learning", but different tasks)
- Negative distinct pairs (completely different projects)
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ----------------------------------------------------------------------
# 1. DEV / CALIBRATION SET (14 pairs: 7 duplicates, 7 distinct)
# ----------------------------------------------------------------------
DEV_SET = [
    # Positive paraphrased
    {
        "id": "dev_pos_1",
        "p1": {"title": "Student Result Analysis Using Machine Learning", "desc": "Predicts student academic grades based on past semester scores using regression."},
        "p2": {"title": "Academic Performance Forecasting with Predictive Analytics", "desc": "Analyzes student semester marks and forecasts academic outcomes using ML."},
        "label": 1
    },
    {
        "id": "dev_pos_2",
        "p1": {"title": "Face Recognition Attendance System", "desc": "Automated student attendance tracking using computer vision and camera feed."},
        "p2": {"title": "Biometric Presence Tracking via Facial Detection", "desc": "Smart classroom attendance monitoring leveraging facial recognition algorithms."},
        "label": 1
    },
    {
        "id": "dev_pos_3",
        "p1": {"title": "Online Voting System with Blockchain Security", "desc": "Decentralized election polling application using smart contracts and Ethereum."},
        "p2": {"title": "Decentralized Ballot and Polling Platform on Distributed Ledger", "desc": "Secure electronic voting infrastructure utilizing smart contract cryptography."},
        "label": 1
    },
    {
        "id": "dev_pos_4",
        "p1": {"title": "Automated Resume Screener and Ranking Tool", "desc": "Parses candidate CV documents and ranks resumes against job descriptions."},
        "p2": {"title": "Curriculum Vitae Parser and Candidate Scoring System", "desc": "Extracts applicant information from resumes and scores job applicants."},
        "label": 1
    },
    {
        "id": "dev_pos_5",
        "p1": {"title": "Traffic Congestion Prediction Using Deep Learning", "desc": "Forecasts urban vehicular road traffic flow using neural time series."},
        "p2": {"title": "Urban Road Traffic Density Forecasting with Deep Neural Networks", "desc": "Estimates city street vehicle jams using highway surveillance sensors."},
        "label": 1
    },
    {
        "id": "dev_pos_6",
        "p1": {"title": "AI Based Smart Parking Space Management", "desc": "Detects available parking slots in mall garages using camera vision."},
        "p2": {"title": "Automated Car Parking Lot Allocation with Computer Vision", "desc": "Identifies empty vehicle parking bays using overhead surveillance video."},
        "label": 1
    },
    {
        "id": "dev_pos_7",
        "p1": {"title": "Sentiment Analysis of Twitter Customer Feedback", "desc": "Classifies social media product tweets into positive or negative polarity."},
        "p2": {"title": "Customer Opinion Mining on Social Media Posts", "desc": "Determines public consumer sentiment from microblog status updates."},
        "label": 1
    },
    # Negative hard pairs (lexical overlap / shared template words, but DIFFERENT problems)
    {
        "id": "dev_neg_1",
        "p1": {"title": "Crop Disease Detection Using Deep Learning", "desc": "Identifies leaf diseases in agricultural crops using CNN models."},
        "p2": {"title": "Brain Tumor Segmentation Using Deep Learning", "desc": "Segments medical MRI brain scans for tumor diagnosis using CNN models."},
        "label": 0
    },
    {
        "id": "dev_neg_2",
        "p1": {"title": "Student Result Analysis Using Machine Learning", "desc": "Predicts student GPA and exam scores from study habits and historical marks."},
        "p2": {"title": "Credit Card Fraud Detection Using Machine Learning", "desc": "Identifies fraudulent financial transactions on credit cards using anomaly models."},
        "label": 0
    },
    {
        "id": "dev_neg_3",
        "p1": {"title": "Face Recognition Attendance System", "desc": "Logs student attendance using webcams and facial recognition."},
        "p2": {"title": "Gesture Recognition for Sign Language Translation", "desc": "Translates deaf sign language gestures into text using computer vision."},
        "label": 0
    },
    {
        "id": "dev_neg_4",
        "p1": {"title": "Movie Recommendation System", "desc": "Recommends films to users based on collaborative filtering and watch history."},
        "p2": {"title": "Music Genre Classification System", "desc": "Categorizes audio MP3 files into jazz, rock, and pop genres using spectrograms."},
        "label": 0
    },
    {
        "id": "dev_neg_5",
        "p1": {"title": "Online Shopping Management System", "desc": "E-commerce store with product catalogs, shopping cart, and payments."},
        "p2": {"title": "Hospital Patient Management System", "desc": "Manages hospital inpatient admissions, room allocations, and doctor rounds."},
        "label": 0
    },
    {
        "id": "dev_neg_6",
        "p1": {"title": "Library Book Lending and Inventory System", "desc": "Tracks book borrowing, returns, and catalog indexing in college libraries."},
        "p2": {"title": "Autonomous Drone Path Planning in 3D Environments", "desc": "Calculates collision-free flight trajectories for quadcopters across obstacles."},
        "label": 0
    },
    {
        "id": "dev_neg_7",
        "p1": {"title": "Real-Time Chat Application with WebSockets", "desc": "Instant messaging web app with group rooms and notifications."},
        "p2": {"title": "Solar Panel Energy Output Estimation", "desc": "Forecasts photovoltaic power generation using meteorological sunlight measurements."},
        "label": 0
    },
]

# ----------------------------------------------------------------------
# 2. HELD-OUT TEST SET (20 pairs: 10 duplicates, 10 distinct)
# ----------------------------------------------------------------------
HELD_OUT_TEST_SET = [
    # Positive: exact / near exact
    {
        "id": "test_pos_1",
        "p1": {"title": "Fake News Detection Using Natural Language Processing", "desc": "Classifies online news articles as legitimate or deceptive using text analysis."},
        "p2": {"title": "Fake News Detection Using NLP", "desc": "Identifies false and misleading news articles using natural language models."},
        "label": 1
    },
    {
        "id": "test_pos_2",
        "p1": {"title": "Heart Disease Risk Prediction System", "desc": "Estimates cardiovascular illness probability from patient clinical records."},
        "p2": {"title": "Cardiac Illness Probability Forecasting Tool", "desc": "Assesses patient heart health and cardiovascular failure risk from medical data."},
        "label": 1
    },
    # Positive: paraphrased duplicates
    {
        "id": "test_pos_3",
        "p1": {"title": "Crop Disease Detection Using Deep Learning", "desc": "Detects leaf fungal and viral infections from plant photos using CNNs."},
        "p2": {"title": "Agricultural Plant Pathology Identification through Neural Networks", "desc": "Automated diagnosis of botanical diseases from foliage imagery with deep models."},
        "label": 1
    },
    {
        "id": "test_pos_4",
        "p1": {"title": "Network Intrusion Detection Using Random Forest", "desc": "Monitors packet traffic and identifies malicious cyber attacks using machine learning."},
        "p2": {"title": "Cyber Attack Identification in Traffic Logs with Ensemble Trees", "desc": "Detects network penetration and unauthorized activity using classifier ensembles."},
        "label": 1
    },
    {
        "id": "test_pos_5",
        "p1": {"title": "Automated Essay Grading and Evaluation System", "desc": "Scores student written essays and provides linguistic feedback using NLP algorithms."},
        "p2": {"title": "AI Powered Descriptive Essay Assessment Platform", "desc": "Analyzes written student prose and assigns automated grades based on coherence."},
        "label": 1
    },
    {
        "id": "test_pos_6",
        "p1": {"title": "Stock Market Price Forecasting Using LSTM", "desc": "Predicts next-day equity share valuations from historical candlestick price sequences."},
        "p2": {"title": "Equity Share Value Trend Prediction with Recurrent Neural Networks", "desc": "Forecasts stock exchange ticker price movements using sequential time-series deep learning."},
        "label": 1
    },
    {
        "id": "test_pos_7",
        "p1": {"title": "Smart Home Automation with IoT and Voice Control", "desc": "Controls domestic appliances via voice commands and ESP8266 microcontroller relays."},
        "p2": {"title": "Voice Operated Domestic Appliance Automation through Internet of Things", "desc": "Operates household lights and fans using speech recognition and connected microcontrollers."},
        "label": 1
    },
    {
        "id": "test_pos_8",
        "p1": {"title": "Driver Drowsiness Detection System with OpenCV", "desc": "Alerts sleeping automobile drivers by tracking eye blink rates in real-time camera streams."},
        "p2": {"title": "Motorist Sleepiness and Fatigue Monitoring via Facial Camera", "desc": "Monitors eye closure duration and yawns to warn sleepy vehicle drivers in real time."},
        "label": 1
    },
    {
        "id": "test_pos_9",
        "p1": {"title": "E-Commerce Product Recommendation Engine", "desc": "Suggests relevant retail goods to online shoppers using user purchase collaborative filtering."},
        "p2": {"title": "Online Marketplace Personalized Item Recommender", "desc": "Offers tailored merchandise suggestions to buyers based on historical shopping cart items."},
        "label": 1
    },
    {
        "id": "test_pos_10",
        "p1": {"title": "Automated Plant Leaf Health Monitoring System", "desc": "IoT soil and camera system measuring leaf moisture and chlorosis discoloration."},
        "p2": {"title": "Botanical Foliage Health and Vitality Tracker with Sensors", "desc": "Monitors plant leaf wellness and water stress utilizing agricultural optical sensors."},
        "label": 1
    },

    # Negative: shared templates / common academic jargon, but completely DIFFERENT tasks
    {
        "id": "test_neg_1",
        "p1": {"title": "Air Quality Index Forecasting Using LSTM", "desc": "Predicts urban PM2.5 atmospheric pollution levels from sensor time series."},
        "p2": {"title": "Stock Market Price Forecasting Using LSTM", "desc": "Predicts equity share valuations from financial ticker price histories."},
        "label": 0
    },
    {
        "id": "test_neg_2",
        "p1": {"title": "Traffic Sign Recognition with Convolutional Networks", "desc": "Classifies highway speed limits and stop signs for driverless vehicle navigation."},
        "p2": {"title": "Handwritten Digit Recognition with Convolutional Networks", "desc": "Recognizes handwritten numerical characters on postal mail envelopes."},
        "label": 0
    },
    {
        "id": "test_neg_3",
        "p1": {"title": "Student Performance Prediction Using Machine Learning", "desc": "Forecasts college GPA and exam outcomes based on attendance and assignments."},
        "p2": {"title": "Product Demand Prediction Using Machine Learning", "desc": "Estimates supply chain retail warehouse restocking requirements using sales figures."},
        "label": 0
    },
    {
        "id": "test_neg_4",
        "p1": {"title": "Face Recognition Attendance System", "desc": "Records student classroom presence using computer vision facial biometric verification."},
        "p2": {"title": "Automated Plant Leaf Health Monitoring System", "desc": "Analyzes crop greenhouse leaves using computer vision and environmental sensors."},
        "label": 0
    },
    {
        "id": "test_neg_5",
        "p1": {"title": "Blockchain Based Land Registry and Verification", "desc": "Records real estate deed ownership and title transfers immutably on Ethereum."},
        "p2": {"title": "Blockchain Based Medical Record Sharing", "desc": "Provides patient-controlled access to hospital health electronic histories."},
        "label": 0
    },
    {
        "id": "test_neg_6",
        "p1": {"title": "Fake News Detection Using Natural Language Processing", "desc": "Detects disinformation in political journalism articles using linguistic features."},
        "p2": {"title": "Automated Code Generation Using Natural Language Processing", "desc": "Generates Python programming source code from plain English software specifications."},
        "label": 0
    },
    {
        "id": "test_neg_7",
        "p1": {"title": "Cyber Attack Identification in Traffic Logs with Ensemble Trees", "desc": "Classifies network firewall logs to detect DDoS and unauthorized penetration attacks."},
        "p2": {"title": "Forest Fire Spread Simulation Using Ensemble Trees", "desc": "Models botanical wildfire burnt area based on wind speeds and fuel moisture."},
        "label": 0
    },
    # Negative: completely distinct domains
    {
        "id": "test_neg_8",
        "p1": {"title": "Employee Payroll and Tax Calculation System", "desc": "Calculates monthly salary deductions, leave balances, and tax withholdings."},
        "p2": {"title": "Underwater Robotic Submarine Navigation with Sonar", "desc": "Guides deep sea autonomous submersible mapping coral reefs with acoustic sensors."},
        "label": 0
    },
    {
        "id": "test_neg_9",
        "p1": {"title": "Online Food Ordering and Delivery Portal", "desc": "Connects restaurant menus with customers and live rider GPS location updates."},
        "p2": {"title": "Quantum Key Distribution Protocol Simulation", "desc": "Simulates BB84 photon polarization quantum cryptography over optical fiber."},
        "label": 0
    },
    {
        "id": "test_neg_10",
        "p1": {"title": "Gym Workout Planner and Calorie Tracker", "desc": "Logs personal physical exercise routines and daily macronutrient dietary intake."},
        "p2": {"title": "Seismic Earthquake Wave Arrival Time Estimation", "desc": "Processes seismograph ground vibration sensor waveforms to pinpoint fault tremors."},
        "label": 0
    },
]


def evaluate_engine_pairs(predict_func, dataset):
    """
    Evaluates a prediction function on a dataset.
    predict_func(p1, p2) -> returns (score: float [0..100], is_duplicate: bool)
    Computes confusion matrix, Precision, Recall, F1, Accuracy.
    """
    tp = fp = fn = tn = 0
    results = []

    for item in dataset:
        p1 = item["p1"]
        p2 = item["p2"]
        ground_truth = item["label"]
        score, is_dup = predict_func(p1, p2)

        if is_dup and ground_truth == 1:
            tp += 1
            verdict = "TP"
        elif is_dup and ground_truth == 0:
            fp += 1
            verdict = "FP"
        elif not is_dup and ground_truth == 1:
            fn += 1
            verdict = "FN"
        else:
            tn += 1
            verdict = "TN"

        results.append({
            "id": item["id"],
            "p1": p1["title"],
            "p2": p2["title"],
            "score": score,
            "pred": 1 if is_dup else 0,
            "truth": ground_truth,
            "verdict": verdict,
        })

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    acc = (tp + tn) / len(dataset) if dataset else 0.0

    return {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": acc,
        "results": results,
    }


def run_benchmark():
    from ml_engine import engine

    def baseline_predict(p1, p2):
        # Baseline: lexical title matching with 55% threshold
        p1_proc, _ = engine.preprocess(p1["title"])
        p2_proc, _ = engine.preprocess(p2["title"])
        tf, _ = engine.tfidf_cosine_similarity(p1_proc, p2_proc, [p1_proc, p2_proc])
        jc, _ = engine.jaccard_similarity(p1_proc, p2_proc)
        sq, _ = engine.sequence_similarity(p1_proc, p2_proc)
        comb = round((tf * 0.45 + jc * 0.30 + sq * 0.25) * 100)
        is_exact = p1["title"].strip().lower() == p2["title"].strip().lower()
        if is_exact:
            comb = 100
        is_dup = (comb >= 55) or is_exact
        return comb, is_dup

    def improved_predict(p1, p2):
        # Improved: multi-field semantic hybrid engine
        # Flagged if Needs Review or High Risk (>= 42%)
        res = engine.compare_proposals(
            new_title=p1["title"],
            existing_title=p2["title"],
            new_description=p1.get("desc", ""),
            existing_description=p2.get("desc", ""),
        )
        is_dup = res["similarity"] >= engine.REVIEW_THRESHOLD or res.get("is_exact_match")
        return res["similarity"], is_dup

    print("=" * 65)
    print("  SIMILARITY BENCHMARK: BASELINE vs IMPROVED ENGINE")
    print("=" * 65)

    base_dev = evaluate_engine_pairs(baseline_predict, DEV_SET)
    base_test = evaluate_engine_pairs(baseline_predict, HELD_OUT_TEST_SET)

    imp_dev = evaluate_engine_pairs(improved_predict, DEV_SET)
    imp_test = evaluate_engine_pairs(improved_predict, HELD_OUT_TEST_SET)

    print("\n[1] DEVELOPMENT / CALIBRATION SET (14 pairs: 7 duplicates, 7 distinct):")
    print(f"  Baseline:  P={base_dev['precision']:.4f}  R={base_dev['recall']:.4f}  F1={base_dev['f1']:.4f}  (TP={base_dev['tp']} FP={base_dev['fp']} FN={base_dev['fn']} TN={base_dev['tn']})")
    print(f"  Improved:  P={imp_dev['precision']:.4f}  R={imp_dev['recall']:.4f}  F1={imp_dev['f1']:.4f}  (TP={imp_dev['tp']} FP={imp_dev['fp']} FN={imp_dev['fn']} TN={imp_dev['tn']})")

    print("\n[2] HELD-OUT TEST SET (20 pairs: 10 duplicates, 10 distinct):")
    print(f"  Baseline:  P={base_test['precision']:.4f}  R={base_test['recall']:.4f}  F1={base_test['f1']:.4f}  (TP={base_test['tp']} FP={base_test['fp']} FN={base_test['fn']} TN={base_test['tn']})")
    print(f"  Improved:  P={imp_test['precision']:.4f}  R={imp_test['recall']:.4f}  F1={imp_test['f1']:.4f}  (TP={imp_test['tp']} FP={imp_test['fp']} FN={imp_test['fn']} TN={imp_test['tn']})")

    print("\n[3] HELD-OUT TEST SET DETAILED PREDICTIONS:")
    for r in imp_test["results"]:
        print(f"  [{r['verdict']}] Score={r['score']:2d}% | Truth={r['truth']} | {r['p1'][:33]} <-> {r['p2'][:33]}")

    return {
        "base_test": base_test,
        "imp_test": imp_test,
    }


if __name__ == "__main__":
    run_benchmark()
