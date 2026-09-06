# Tradie in trAIning — Setup & Run

## 1. Install dependencies
```
pip3 install -r requirements.txt
```

## 2. Set your Anthropic API key
Mac/Linux:
```
export ANTHROPIC_API_KEY="your-key-here"
```
Windows (PowerShell):
```
setx ANTHROPIC_API_KEY "your-key-here"
```
(get a key at console.anthropic.com if you don't have one yet — or swap the
`anthropic.Anthropic()` client and model calls for OpenAI's if that's what
your team already has access to)

## 3. Run it
```
streamlit run app.py
```
It'll open automatically in your browser (usually http://localhost:8501).

## How it works
1. Student uploads a file (PDF, Word, PowerPoint, text, or an image of a
   diagram/handwritten notes).
2. Text-based files are parsed directly. Image files are sent to a
   vision-capable Claude model to describe their content first.
3. The extracted material is sent to Claude, which breaks it into 3–6
   checkpoints, each with a guiding question, a hint, and a full explanation.
4. The student answers each checkpoint, gets brief feedback, and only sees
   the full explanation once they've had a go — grounded entirely in their
   own uploaded material, not a generic AI answer.

## Known limitations (worth stating in your pitch, not hiding)
- Handles one file at a time in this prototype — combining multiple files
  into one session is a reasonable "next step."
- Image analysis quality depends on how clear the photo/scan is.
- No login/accounts — fine for a hackathon demo, would need auth for
  real deployment.
- Checkpoint generation quality depends on how well-structured the source
  material is.
