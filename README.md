<div align="center">

# ✈️ Trip Planner — Next-Gen Multi-Agent Travel Planner

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Parallel%20Multi--Agent-orange.svg)](https://www.langchain.com/langgraph)
[![Groq](https://img.shields.io/badge/Groq-Ultra--Fast%20Inference-f55036.svg)](https://groq.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Render%20Persistence-336791.svg)](https://www.postgresql.org/)

**An autonomous multi-agent travel intelligence platform that plans complete, actionable trips in seconds — featuring real-time flight scouting, handpicked stays, day-by-day itineraries, and itemized budget estimates.**

<br />

<!-- Auto-playing Demo GIF -->
<img src="assets/tripmate_demo.gif" alt="TripMate AI Live Demo" width="100%" style="border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);" />

<br />

[Features](#-key-features) • [Architecture](#-multi-agent-architecture) • [Getting Started](#-getting-started) • [Environment Setup](#-environment-variables) • [Tech Stack](#-tech-stack)

</div>

---

## 🌟 Key Features

- **⚡ Parallel Multi-Agent Orchestration**: Powered by **LangGraph**, executing live flight searches and hotel scouting simultaneously to cut total latency in half.
- **🛫 Live Flight Radar**: Real-time airline route exploration with origin/destination IATA code resolution, departure schedules, and flight numbers via **AviationStack API** (with offline resilient fallbacks).
- **🏨 Premier Accommodations**: Intelligent hotel and resort scouting with amenities, locations, and pricing insights via **Tavily Web Search API**.
- **📅 Exhaustive Day-by-Day Masterplans**: Structured itineraries with morning, afternoon, and evening breakdowns, local food recommendations, and transit advice.
- **💰 Smart Budget Estimator**: Itemized travel expense breakdowns (Flights, Stays, Meals, Transit, Sightseeing) with budget vs. luxury ranges.
- **💾 Long-Term Session Persistence**: Stateful conversation checkpointing powered by **PostgreSQL (Render)** and LangGraph `PostgresSaver`.
- **🎨 Modern Dark Glassmorphic UI**: Real-time agent progress tracker, Markdown formatting, one-click clipboard copying, PDF export, and pre-built destination prompts.

---

## 🧠 Multi-Agent Architecture

TripMate AI uses a **parallel fan-out / fan-in** directed acyclic graph (DAG):

```text
               ┌────────────────────────┐
               │   START (User Query)   │
               └───────────┬────────────┘
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
   ┌───────────────────┐       ┌───────────────────┐
   │   Flight Agent    │       │    Hotel Agent    │
   │  (AviationStack)  │       │     (Tavily)      │
   └─────────┬─────────┘       └─────────┬─────────┘
             │                           │
             └─────────────┬─────────────┘
                           ▼
               ┌───────────────────────┐
               │     Planner Agent     │
               │  (openai/gpt-oss-120b)│
               └───────────┬───────────┘
                           ▼
               ┌───────────────────────┐
               │    END (Masterplan)   │
               └───────────────────────┘
```

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/akashverma1995/Trip-Planner-Agent.git
cd Trip-Planner-Agent
```

### 2. Set up virtual environment

- **Windows (Command Prompt / PowerShell):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\activate
  ```

- **macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 3. Install dependencies
```bash
python -m pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:

```env
# LLM Inference
GROQ_API_KEY="your_groq_api_key_here"
LLM_MODEL=openai/gpt-oss-120b
MAX_OUTPUT_TOKENS=5000

# Live Data APIs
AVIATIONSTACK_API_KEY=your_aviationstack_key_here
TAVILY_API_KEY=your_tavily_key_here
DEFAULT_ORIGIN_IATA=DEL

# Checkpointer Persistence (Render PostgreSQL)
DATABASE_URL=postgresql://user:password@hostname/database?sslmode=require
```

### 5. Run the Application
```bash
python app.py
```

Open your browser and navigate to:
```
http://localhost:8000
```

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| **Orchestration** | [LangGraph](https://www.langchain.com/langgraph) | Parallel multi-agent graph with state management |
| **LLM Provider** | [Groq](https://groq.com/) | Sub-second high-throughput LLM inference (`gpt-oss-120b`) |
| **Backend Framework**| [FastAPI](https://fastapi.tiangolo.com/) | Async non-blocking REST API with Pydantic contracts |
| **Flight Intelligence**| [AviationStack API](https://aviationstack.com/) | Live airline flights & schedule tracking |
| **Search Intelligence**| [Tavily AI](https://tavily.com/) | Targeted search engine optimized for AI agents |
| **Persistence** | [PostgreSQL](https://www.postgresql.org/) (Render) | Stateful multi-turn conversation checkpointer |
| **Frontend** | Vanilla JS + HTML5 + CSS3 | Glassmorphic dark UI with live step tracker and PDF generation |

---

## 📄 License
This project is licensed under the MIT License.
