# Gridfinity AI — The Parametric Organizer Engine

A web-based SaaS application that generates **print-ready Gridfinity bins** from natural language descriptions, powered by AI and parametric CAD.

## Architecture

```
frontend/  → Next.js + React + Three.js (3D preview)
backend/   → Python FastAPI + CadQuery (parametric engine)
```

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
# Server runs at http://localhost:8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# App runs at http://localhost:3000
```

### Environment Variables
- `GEMINI_API_KEY` — (optional) Gemini 1.5 Pro API key for AI-powered generation. Without it, the app uses a deterministic mock engine.

## Features
- 🗣️ Natural language bin descriptions
- 📐 Parametric CAD generation (CadQuery / fallback)
- 🧰 Built-in tool library (20+ items with verified dimensions)
- 🛡️ Printability guardrails (wall thickness, depth limits, overlap detection)
- 🧊 Real-time 3D preview in the browser
- 📥 STL download for 3D printing
