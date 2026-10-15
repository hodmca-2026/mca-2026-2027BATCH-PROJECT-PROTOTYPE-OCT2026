# 🌿 ByYourSide

 **Notice. Understand. Respond.**

ByYourSide is a **mental health awareness and support guidance web application** designed for friends, family members, and concerned individuals who notice changes in someone's behavior or communication.

Users can describe what they have observed, and the application uses an **ML/NLP model** to classify the submitted text based on patterns supported by its training data. It then provides supportive guidance on how to approach and support the person.

> ⚠️ **Disclaimer:** ByYourSide is an awareness and support guidance system. It is **not a medical diagnosis system, suicide prediction system, or mental illness diagnosis tool.**

---

## ✨ Features

### 👤 User Features
- 🔐 User Registration & Login
- 🪪 JWT Authentication
- 🛡️ Protected Routes
- 📝 Text-based Assessment
- 🤖 ML-powered Text Classification
- 📊 Result Display
- 💬 Supportive Guidance
- 🗣️ "What Should I Say?" Guidance
- 📜 Assessment History
- 🔎 View Previous Results
- 🌙 Light & Dark Mode
- 📱 Responsive UI

### 👨‍💼 Admin Features
- 🔐 Admin Authentication
- 📊 Admin Dashboard
- 👥 User Management
- 🔄 User Role Management
- 📋 Assessment Management
- 📈 Analytics
- 📊 Prediction Distribution
- 📅 Daily Assessment Statistics

### 🔒 Security
- JWT-based authentication
- Password hashing with bcrypt
- Role-based authorization
- Admin-only routes
- User assessment ownership protection
- Input validation
- Parameterized SQL queries
- Restricted CORS
- Protected admin role changes

---

## 🏗️ Architecture

```text
                 ┌──────────────────┐
                 │   React + Vite   │
                 │    Frontend      │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Node.js +        │
                 │ Express Backend  │
                 └───────┬─────┬────┘
                         │     │
              ┌──────────┘     └──────────┐
              ▼                           ▼
       ┌──────────────┐          ┌────────────────┐
       │    MySQL     │          │ FastAPI ML API │
       │   Database   │          │                │
       └──────────────┘          └───────┬────────┘
                                         │
                                         ▼
                                  ┌──────────────┐
                                  │ Trained ML   │
                                  │ Model + TFIDF│
                                  └──────────────┘
