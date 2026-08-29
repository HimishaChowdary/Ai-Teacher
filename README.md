
The model is explicitly instructed not to invent facts outside the
uploaded document, and to return machine-readable JSON so the app can
reliably build the quiz UI from it.

## Tech stack

- **Python**
- **Streamlit** — turns the Python script into a web app with no
  HTML/CSS/JS needed
- **Google Gemini API** (`gemini-3.6-flash`) — generates the questions,
  options, correct answers, and explanations
- **pypdf** — extracts text from the uploaded PDF

## Setup

1. Clone this repo and move into it:
```bash
   git clone <this-repo-url>
   cd ai-teacher
```

2. Create a virtual environment (keeps this project's packages separate
   from everything else on your computer):
```bash
   python -m venv venv
   source venv/bin/activate      # on Windows: venv\Scripts\activate
```

3. Install the dependencies:
```bash
   pip install -r requirements.txt
```

4. Get a free Google Gemini API key from https://aistudio.google.com
   (just needs a Google account, no credit card, no billing required
   on the free tier).

5. Set your API key as an environment variable (recommended, so you
   never have to paste it into the app):
```bash
   export GOOGLE_API_KEY="your-key-here"     # on Windows: set GOOGLE_API_KEY=your-key-here
```
   Alternatively, just paste it into the sidebar field when the app
   opens — it's only kept for that session and never saved.

## Running it

```bash
streamlit run app.py
```

This opens the app in your browser at `http://localhost:8501`.

## Screenshot

<img width="1916" height="857" alt="image" src="https://github.com/user-attachments/assets/7babcf85-f397-405e-95ca-38b3a5e5ea94" />
<img width="1912" height="866" alt="ai teacher" src="https://github.com/user-attachments/assets/02a30ddb-8c05-4444-9f48-b8bb608c0d39" />

## Known limitations

- Scanned/image-only PDFs won't work since `pypdf` only extracts
  selectable text, not text inside images (OCR is a possible future
  addition).
- Very long PDFs are trimmed to the first ~12,000 characters to keep
  the request within a reasonable size — good for a single chapter or
  a set of notes, not an entire textbook.
- Google frequently updates/retires Gemini model names — if you get a "model not found" error, check aistudio.google.com/models for the current model name and update it in `app.py`.

## Possible next steps

- Add OCR support for scanned PDFs (e.g. via `pytesseract`)
- Let the user choose difficulty level
- Support multiple question types (true/false, short answer)
