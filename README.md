# YouTube Content Generator

A Streamlit app that uses Gemini AI to generate SEO-friendly YouTube titles, descriptions, tags, and thumbnail ideas.

## Features

- Generate 8 optimized titles  
- Write long-form SEO descriptions  
- Create keyword-based tag sets  
- Suggest thumbnail design concepts  

## Setup Instructions

### 1. Install Requirements

```bash
python -m pip install -r requirements.txt
```

### 2. Add API Key

Create a file at `.streamlit/secrets.toml` and add:

```toml
GEMINI_API_KEY = "your_api_key_here"
```

### 3. Run the App

```bash
streamlit run app.py
```

## Sample Test Case

- Script: "How to learn Python from scratch in 30 days"  
- Video Type: Tutorial  
- Audience: Beginners  
- Tone: Educational  
- Keywords: Python, programming, beginner

## Link
 - https://gen-ai-youtube-content-generator-abi-karimireddy.streamlit.app/
