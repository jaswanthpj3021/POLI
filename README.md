# Campus Cashflow Planner (College Project)

A simple full-stack expense tracker + budget planner built with:
- **Python (Flask)** backend API
- **ReactJS + HTML + CSS + JavaScript** frontend

## Features
- Animated **Login / Signup** interface
- Add and view **budget plans**
- Add and view **expenses/transactions**
- Add **expense notes** and optional **image URLs**
- **Profile** page with summary stats
- **Notes** page for personal planning
- **Chat corner** to connect with other users
- **Light / Dark theme** toggle

## Run in VS Code
1. Open this folder in VS Code.
2. Open a terminal and run:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
```

3. Open browser: `http://localhost:5000`

## Project Structure
- `backend/app.py` - Flask API, auth, SQLite models
- `frontend/index.html` - React mount + CDN imports
- `frontend/static/app.jsx` - React app pages/components
- `frontend/static/styles.css` - themed animated UI

## Notes
- Data is stored in `backend/expense_planner.db` (SQLite).
- Good starter template for mini/major college project submissions.
