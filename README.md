# AI Technical Learning Mentor

A complete, beginner-friendly AI-powered technical learning platform built with Python,
LangChain, OpenRouter, Streamlit, SQLite, and LangSmith.

---

## 🎯 Project Objective

The AI Technical Learning Mentor helps students learn technical concepts through a
structured process:

1. **AI teaches** a topic (beginner-friendly explanation)
2. **AI generates** a practical, real-world scenario
3. **Student submits** their answer
4. **AI evaluates** the answer with scores and feedback
5. **AI recommends** personalized next topics

This is **not** a generic chatbot — it follows a fixed learning loop so students
understand, apply, and receive feedback on every concept.

---

## ✨ Features

- **AI Topic Explanations** – Structured lessons with definitions, examples, architecture, and more
- **Practical Scenarios** – Realistic technical situations at beginner/intermediate/advanced levels
- **Answer Evaluation** – Scored feedback (0–10) with strengths, weaknesses, and corrections
- **Personalized Recommendations** – Next topics based on your actual results
- **Learning History** – Persistent session history in SQLite
- **Progress Dashboard** – Real charts and stats from your actual data
- **LangSmith Tracing** – Monitor every LangChain execution

---

## 🛠 Technology Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.13 |
| LLM Framework | LangChain, langchain-openai |
| LLM Provider | OpenRouter (via ChatOpenAI) |
| Frontend | Streamlit |
| Database | SQLite |
| Environment | python-dotenv |
| Monitoring | LangSmith |
| Testing | pytest, pytest-mock |

---

## 📁 Folder Structure

```
AI_Technical_Mentor/
├── app.py                 # Streamlit application entry point
├── run.ps1                # PowerShell script to run the app
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── .env                   # Your secret API keys (not committed)
├── .env.example           # Template for .env
├── .gitignore             # Files to exclude from Git
├── learning_mentor.db     # SQLite database (created at runtime)
│
├── chains/
│   ├── __init__.py
│   ├── llm.py             # OpenRouter LLM connection
│   ├── teaching_chain.py  # Topic explanation chain
│   ├── scenario_chain.py  # Scenario generation chain
│   └── evaluation_chain.py# Answer evaluation chain
│
├── database/
│   ├── __init__.py
│   ├── db.py              # SQLite connection + schema
│   └── operations.py      # CRUD operations for sessions, answers, evaluations
│
├── prompts/
│   ├── __init__.py
│   └── templates.py       # LangChain prompt templates
│
├── utils/
│   ├── __init__.py
│   ├── config.py          # Environment variable loading & validation
│   └── validators.py      # Input validation helpers
│
└── tests/
    ├── __init__.py
    └── test_chains.py     # Automated tests (uses mocks, no paid API calls)
```

---

## ⚙️ Installation

### 1. Open the project folder in VS Code

Open `C:\Users\HP\Documents\visualstudiocode\AI_Technical_Mentor` in VS Code.

### 2. Activate the virtual environment

The `.venv` folder already exists. Activate it in PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure your API keys

Copy the example file:

```powershell
copy .env.example .env
```

Then edit `.env` and add your OpenRouter API key:

```
OPENROUTER_API_KEY=sk-or-your-actual-key-here
OPENROUTER_MODEL=openrouter/auto

LANGSMITH_TRACING=true
LANGSMITH_API_KEY=ls-your-langsmith-key
LANGSMITH_PROJECT=AI-Technical-Mentor
```

> ⚠️ Never share your `.env` file. It is already in `.gitignore`.

---

## ▶️ How to Run

### Option A: Using the PowerShell script

```powershell
.\run.ps1
```

### Option B: Manually

```powershell
.venv\Scripts\Activate.ps1
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

---

## 🔗 How LangChain Is Used

Three separate chains are built with LangChain Expression Language (LCEL) pipe syntax:

1. **Teaching Chain** (`chains/teaching_chain.py`)
   - Input: topic name
   - Output: structured beginner-friendly explanation
   - Prompt: `TEACHING_PROMPT`

2. **Scenario Chain** (`chains/scenario_chain.py`)
   - Input: topic, explanation, difficulty
   - Output: practical real-world scenario
   - Prompt: `SCENARIO_PROMPT`

3. **Evaluation Chain** (`chains/evaluation_chain.py`)
   - Input: topic, scenario, student answer
   - Output: structured JSON evaluation (scores + feedback)
   - Prompt: `EVALUATION_PROMPT`

Each chain is: `prompt | llm | StrOutputParser()`.

---

## 🌐 How OpenRouter Is Connected

`chains/llm.py` creates a `ChatOpenAI` client pointed at OpenRouter:

```python
ChatOpenAI(
    model=OPENROUTER_MODEL,
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)
```

The model ID comes from `OPENROUTER_MODEL` in your `.env` (default: `openrouter/auto`).
The API key is never hardcoded and is masked in the UI.

---

## 🔍 How LangSmith Tracing Works

When `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY` are set, the app enables
LangChain tracing. Every chain run is recorded in your LangSmith project so you can:

- See inputs and outputs for each step
- Check execution latency
- Inspect token usage
- Debug errors

View traces at: https://smith.langchain.com → your project (`AI-Technical-Mentor`)

If LangSmith is not configured, the app runs normally without tracing.

---

## 💾 SQLite Database

All learning data is stored locally in `learning_mentor.db`:

| Table | Stores |
|-------|--------|
| `learning_sessions` | Topic, difficulty, status, timestamps |
| `topic_explanations` | AI-generated lesson text |
| `scenarios` | Generated practical scenarios |
| `student_answers` | Your submitted answers |
| `evaluations` | Scores, feedback, recommendations |

Data persists across app restarts. All SQL uses parameterized queries.

---

## 🧪 Testing

Run the test suite (uses mocks — no paid API calls required):

```powershell
pytest
```

Tests cover:
- Database creation and CRUD
- Session and evaluation storage/retrieval
- Input validation
- Chain construction
- API key error handling

---

## 🚀 Deployment (Streamlit Community Cloud)

1. Push this repo to GitHub (`.env` is ignored — do not commit it)
2. Go to https://streamlit.io/cloud and connect your repo
3. Add secrets in the Streamlit Cloud dashboard:
   - `OPENROUTER_API_KEY`
   - `OPENROUTER_MODEL`
   - `LANGSMITH_TRACING`
   - `LANGSMITH_API_KEY`
   - `LANGSMITH_PROJECT`
4. Deploy. The app runs `streamlit run app.py`.

---

## 🔧 Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: streamlit` | Run `pip install -r requirements.txt` |
| Missing API key error | Add `OPENROUTER_API_KEY` to `.env` and restart |
| LangSmith warning | Add `LANGSMITH_API_KEY` or set `LANGSMITH_TRACING=false` |
| Database locked | Close other app instances using the `.db` file |

---

## 🔮 Future Enhancements

- User accounts and authentication
- Export learning history to PDF
- More LLM model options
- Code execution sandbox for programming topics
- Spaced-repetition review schedule

---

## 📄 License

MIT License. Built for learning purposes.
