# Fake Job Listing Detector (Web Crawler + Autoencoder)

## Setup (once)
1. `pip install -r requirements.txt`
2. Download the Kaggle "Real / Fake Job Posting Prediction" dataset and put
   `fake_job_postings.csv` in this folder.
3. `python train.py`   -> creates `autoencoder.keras` and `meta.pkl`

## Run
1. `python server.py`
2. Chrome -> `chrome://extensions` -> turn on Developer mode -> Load unpacked -> select the `extension` folder.
3. Open any job listing page. A green/red badge appears top-right.

## Optional: crawler demo
`python crawler.py https://some-job-site.com/jobs 20`  -> saves `crawled_jobs.csv`

## How it works (for viva)
- Web crawler (crawler.py): fetch -> parse with Beautiful Soup -> extract text -> follow links (BFS, same domain).
  Same parser runs on every page the extension sends.
- Autoencoder (train.py): deep + denoising + regularized (L2, dropout). Trained on genuine jobs only.
  High reconstruction error = unusual posting = flagged as fraud (anomaly detection).
- Threshold is picked on a validation set by best F1.
