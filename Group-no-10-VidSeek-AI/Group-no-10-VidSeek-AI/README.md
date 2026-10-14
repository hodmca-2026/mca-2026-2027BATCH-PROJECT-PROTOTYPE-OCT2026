# Group 10 - VidSeek AI 🎥🔍

## Project Details
- **Project Title:** VidSeek AI
- **Group No.:** 10

### Team Members
| Name | Roll No. | Elective |
| :--- | :--- | :--- |
| **Disha Mehtani** | 52138 | Cloud Computing |
| **Chirag Lokhande** | 52136 | Information Retrieval |
| **Yash Talati** | 52065 | Deep Learning |
| **Aniket Kambale** | 52033 | Cloud Computing |

---

## 📌 Project Overview
**VidSeek AI** transforms hours of unstructured video lectures (from YouTube links or local video uploads) into topic-wise mini-videos, synchronized speech transcripts, semantic timestamp search, AI-powered lecture notes, and automated quizzes.

### Key Capabilities:
- **Audio & Video Ingestion**: Native multi-format local uploads (MP4, MKV, WebM, MOV) and YouTube downloads via `yt-dlp`.
- **Speech-to-Text Pipeline**: OpenAI Whisper transcription with accurate word-level and sentence-level timestamps.
- **Smart Topic Segmentation**: NLP text segmentation using TextBlob and SentenceTransformers to detect topic transitions and slice videos losslessly.
- **Semantic Search Engine**: Vector cosine similarity index over transcription chunks to jump directly to the exact second a concept is taught.
- **AI Summary & Quiz Generation**: Automatic concise summary generation, key takeaway bullets, and interactive revision quizzes.

---

## 📁 Repository Structure
```
Group-no-10-VidSeek-AI/
├── README.md                          # Project documentation and group information
├── Group_10_Project_Details.docx      # Official group & project submission details
└── VidSeek/                           # Full VidSeek AI Application Source Code
    ├── app.py                         # Flask web application & API routing
    ├── services/                      # Transcription, segmentation & search modules
    ├── static/                        # Premium UI stylesheets, scripts, and assets
    ├── templates/                     # Jinja2 HTML templates
    ├── requirements.txt               # Dependencies
    ├── Dockerfile                     # Containerization
    └── README.md                      # Detailed technical documentation for VidSeek
```

---

## 🚀 Getting Started

To run the VidSeek AI application locally:

```bash
cd VidSeek
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```
Open your browser and navigate to `http://localhost:5001`.
