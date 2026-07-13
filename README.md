# ✈️ Multi-Agent Smart Trip Planning Assistant

A stateful, multi-user AI trip planning application built with **LangGraph**, **Gemini**, **Model Context Protocol (MCP)**, **Streamlit**, **Pydantic**, **SQLite**, and **OpenWeather API**.

The system coordinates multiple specialized agents to generate personalized, weather-aware, transport-aware, and budget-conscious itineraries. It also supports secure user authentication, user-isolated long-term memory, persistent chat history, budget replanning, and Human-in-the-Loop approval.

---

## 📌 Project Overview

The Multi-Agent Smart Trip Planning Assistant accepts a natural-language request such as:

```text
Plan a trip to Goa from 20 August 2026 to 25 August 2026
for 4 people with a budget of 40000 INR.
```

The system then:

1. Retrieves the logged-in user's previous trips, preferences, and chats.
2. Extracts structured trip requirements from the request.
3. Identifies missing mandatory information.
4. Retrieves current weather and forecast information.
5. Suggests suitable destinations and activities.
6. Creates a practical transport strategy.
7. Estimates the complete trip budget.
8. Pauses for human approval if the estimate exceeds the budget.
9. Replans the trip after approval.
10. Generates a detailed day-wise itinerary.
11. Stores the trip and learned preferences in SQLite.

---

## ✨ Key Features

### Multi-Agent Planning

- Planner Agent
- Weather Agent
- Destination Agent
- Transport Agent
- Budget Agent
- Human Review Agent
- Replanner Agent
- Itinerary Composer Agent
- Memory Retriever Agent
- Memory Saver Agent

### Human-in-the-Loop Budget Review

When the estimated trip cost exceeds the user-entered budget, the LangGraph workflow pauses and presents three choices:

- **Approve Replanning** — reduces optional costs and creates a revised itinerary.
- **Continue Current Plan** — keeps the existing plan despite the higher estimate.
- **Update Budget** — accepts a new budget and recalculates the plan.

The workflow resumes from the saved graph checkpoint instead of restarting from the beginning.

### Long-Term Memory

SQLite stores user-specific:

- Previous trips
- Budget preferences
- Destination history
- Travel style
- Learned preferences
- User and assistant chat history

All stored information is separated using `user_id`, preventing data from different users from colliding.

### Authentication

- Account creation
- User ID and password login
- Password hash storage
- User-isolated memory retrieval
- Session-aware logout and reset

### Real-Time Trip Context

- Current weather
- Temperature and humidity
- Wind and rain information
- Forecast summaries
- Weather-aware activity recommendations
- Indoor alternatives when required

### Streamlit User Interface

- Soft and readable colour scheme
- Login and signup screen
- Editable non-fixed trip request form
- Agent workflow progress in the sidebar
- Previous trips and learned memories
- Recent conversation history
- Formatted weather, budget, transport, and itinerary panels
- Original and revised budget comparison

---

## 🧠 Agent Responsibilities

### 1. Memory Retriever Agent

Loads the authenticated user's:

- Recent trips
- Learned preferences
- Stored chat history

The retrieved context is added to the shared `TripState` before planning begins.

### 2. Planner Agent

Extracts structured information from the user's request:

- Destination
- Origin
- Start and end dates
- Duration
- Number of travelers
- Budget
- Currency
- Travel style
- Preferences
- Missing required fields

If mandatory information is missing, the graph stops and requests the required details.

### 3. Weather Agent

Retrieves current weather and forecast information through the MCP weather integration and OpenWeather API.

### 4. Destination Agent

Suggests:

- Recommended areas
- Suitable activities
- Activities to avoid
- Weather-aware alternatives
- Experience-based recommendations

### 5. Transport Agent

Creates a practical transport plan by:

- Grouping nearby attractions
- Reducing backtracking
- Recommending suitable local transport
- Controlling unnecessary transport expenses

### 6. Budget Agent

Calculates:

- User budget
- Estimated total
- Cost breakdown
- Budget status
- Budget explanation

If the trip exceeds the budget, it routes the workflow to Human Review.

### 7. Human Review Agent

Pauses the graph and waits for the user to:

- Approve replanning
- Continue with the current plan
- Update the budget

### 8. Replanner Agent

After approval, the Replanner:

- Reduces non-essential paid activities
- Replaces luxury transfers
- Reduces premium dining choices
- Preserves essential experiences
- Creates a revised estimated total
- Calculates savings
- Records the changes made

### 9. Itinerary Composer Agent

Combines all agent outputs into a final day-wise itinerary containing:

- Trip summary
- Morning, afternoon, and evening plans
- Notes for each day
- Weather guidance
- Budget summary
- Transport notes
- Trade-offs
- Final recommendation

### 10. Memory Saver Agent

Stores completed trip details and newly learned preferences for future personalization.

---

## 🔄 LangGraph Workflow

```text
Memory Retriever
        ↓
Planner
        ↓
Required details available?
   ├── No  → Request missing information → END
   └── Yes
        ↓
Weather
        ↓
Destination
        ↓
Transport
        ↓
Budget
        ↓
Within budget?
   ├── Yes → Composer
   └── No
        ↓
Human Review
   ├── Approve Replanning → Replanner → Composer
   ├── Continue Current   → Composer
   └── Update Budget      → Budget
        ↓
Memory Saver
        ↓
END
```

---

## 🧱 Technology Stack

- **Python** — primary programming language
- **LangGraph** — multi-agent workflow orchestration
- **LangChain / Gemini** — LLM-based reasoning and structured generation
- **Model Context Protocol (MCP)** — standardized external tool integration
- **Streamlit** — interactive web interface
- **Pydantic** — typed shared state and validation
- **SQLite** — authentication, chat history, and long-term memory
- **OpenWeather API** — weather and forecast information
- **python-dotenv** — environment variable management

---

## 📁 Project Structure

```text
Multi_agent_trip_planner/
│
├── agents/
│   ├── planner_agent.py
│   ├── weather_agent.py
│   ├── destination_agent.py
│   ├── transport_agent.py
│   ├── budget_agent.py
│   ├── human_review_agent.py
│   ├── replanner_agent.py
│   └── itinerary_composer_agent.py
│
├── graph/
│   └── trip_graph.py
│
├── memory/
│   ├── __init__.py
│   ├── auth_manager.py
│   ├── memory_agent.py
│   ├── memory_manager.py
│   ├── memory_schema.py
│   └── memory.db                 # Generated locally; do not commit
│
├── state/
│   └── trip_state.py
│
├── utils/
│   ├── json_utils.py
│   ├── llm_config.py
│   ├── logger_config.py
│   └── mcp_client.py
│
├── app.py
├── requirements.txt
├── .env                          # Local secrets; do not commit
├── .gitignore
└── README.md
```

> The exact MCP server file names may vary depending on the current project structure.

---

## ⚙️ Prerequisites

Before running the application, install:

- Python 3.11 or later
- Git
- A Gemini API key
- An OpenWeather API key

A virtual environment is strongly recommended.

---

## 🚀 Installation and Setup

### 1. Clone the Repository

```powershell
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd Multi_agent_trip_planner
```

### 2. Create a Virtual Environment

```powershell
python -m venv trip_env
```

### 3. Activate the Environment

```powershell
.\trip_env\Scripts\Activate.ps1
```

If PowerShell blocks script execution, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\trip_env\Scripts\Activate.ps1
```

### 4. Install Dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Create the Environment File

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_gemini_api_key
OPENWEATHER_API_KEY=your_openweather_api_key
```

If the code uses different environment variable names, update the `.env` keys to match the variables referenced in `utils/llm_config.py` and the weather integration.

### 6. Run Syntax Validation

```powershell
python -m py_compile .\app.py
python -m py_compile .\state\trip_state.py
python -m py_compile .\graph\trip_graph.py
python -m py_compile .\agents\human_review_agent.py
python -m py_compile .\agents\budget_agent.py
python -m py_compile .\agents\replanner_agent.py
python -m py_compile .\memory\memory_agent.py
```

No output means the files passed syntax validation.

### 7. Start the Application

```powershell
streamlit run app.py
```

Open the local URL displayed in the terminal, normally:

```text
http://localhost:8501
```

---

## 👤 Application Usage

### Create an Account

1. Open the **Sign Up** tab.
2. Enter a unique User ID.
3. Create and confirm a password.
4. Select **Create Account**.

### Log In

1. Open the **Login** tab.
2. Enter the registered User ID and password.
3. Select **Login**.

### Generate a Trip

Enter a request such as:

```text
Plan a trip to Mysore from 10 September 2026 to 13 September 2026
for 2 people with a budget of 30000 INR.
```

### Test Human-in-the-Loop

Use a deliberately low budget:

```text
Plan a trip to Goa from 20 August 2026 to 25 August 2026
for 4 people with a budget of 15000 INR.
```

If the estimate exceeds the budget, choose one of the available Human Review actions.

---

## 🗄️ SQLite Database Design

The database is generated automatically at:

```text
memory/memory.db
```

Main tables include:

### `auth_users`

Stores authentication information:

- `user_id`
- `password_hash`
- `created_at`

### `users`

Stores registered memory users:

- `user_id`
- `created_at`

### `trip_history`

Stores completed trips:

- `user_id`
- `destination`
- `budget`
- `duration`
- `travel_style`
- `created_at`

### `long_term_memory`

Stores learned preferences:

- `user_id`
- `memory_text`
- `memory_type`
- `created_at`

### `chat_history`

Stores conversations:

- `user_id`
- `role`
- `message`
- `created_at`

---

## 🔍 Inspecting the Database

Do not open `memory.db` as a text file. SQLite files are binary and will display unreadable characters.

Use Python instead:

```powershell
python
```

```python
import sqlite3

connection = sqlite3.connect("memory/memory.db")

print(
    connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
)

print(
    connection.execute(
        "SELECT * FROM trip_history"
    ).fetchall()
)

print(
    connection.execute(
        "SELECT * FROM long_term_memory"
    ).fetchall()
)

print(
    connection.execute(
        "SELECT role, message FROM chat_history"
    ).fetchall()
)

connection.close()
```

---

## 🔐 Security Practices

- Never commit `.env`.
- Never commit `memory/memory.db`.
- Never store plain-text passwords.
- Rotate an API key immediately if it appears in logs, screenshots, commits, or chat messages.
- Keep secrets in environment variables.
- Use a stronger password-hashing algorithm such as bcrypt or Argon2 before production deployment.
- Use a production identity provider for deployed applications.

Recommended `.gitignore` entries:

```gitignore
.env
trip_env/
venv/
__pycache__/
*.pyc
logs/
*.log
memory/memory.db
.streamlit/secrets.toml
```

If `memory.db` or `.env` was previously tracked:

```powershell
git rm --cached .\memory\memory.db
git rm --cached .\.env
```

---

## 🧪 Recommended Test Scenarios

### Complete Input

```text
Plan a trip to Goa from 10 August 2026 to 14 August 2026
for a couple with a budget of 40000 INR.
```

Expected result: complete itinerary generation.

### Missing Budget

```text
Plan a trip to Goa from 10 August 2026 to 14 August 2026
for a couple.
```

Expected result: the Planner requests the missing budget.

### Over-Budget Request

```text
Plan a trip to Goa from 10 August 2026 to 16 August 2026
for 4 people with a budget of 12000 INR.
```

Expected result: Human Review is displayed.

### User Isolation

1. Create two user accounts.
2. Generate different trips for each account.
3. Log in separately.
4. Verify that each user sees only their own trips, memories, and chats.

### Persistence

1. Generate a trip.
2. Stop Streamlit.
3. Restart the application.
4. Log in again.
5. Verify that previous trips and chats remain available.

---

## 🛠️ Troubleshooting

### `sqlite3.OperationalError: no such column`

The current database may use an older schema. During development, back up required data and recreate the local database:

```powershell
Remove-Item .\memory\memory.db
streamlit run app.py
```

Do not delete the database in production without a migration and backup plan.

### Sidebar Does Not Refresh

Use the **Refresh** button in the sidebar. Confirm that retrieval functions filter by the logged-in `user_id`.

### Input Text Is Not Visible

Confirm that the Streamlit input CSS uses a white background, dark text, and a visible caret.

### Query Field Contains an Example

The example should be a `placeholder`, not the `value` of the text area.

### Budget Review Does Not Appear

Verify that:

- `human_review_agent.py` exists.
- The graph contains the Human Review node.
- The graph is compiled with a checkpointer.
- Each invocation uses a stable `thread_id`.
- The application resumes using `Command(resume=...)`.

### Duplicate Chat Messages

Chat messages should be saved in one place only. In the current design, `app.py` is the primary chat-history writer, while the Memory Saver Agent stores trips and preferences.

---

## 📚 Learnings

### Multi-Agent Design

- Split a complex task into specialized agents.
- Kept agent responsibilities clear and modular.
- Used shared state instead of direct agent dependencies.

### LangGraph

- Used graph nodes for controlled execution.
- Added conditional routing for missing data and budget checks.
- Added interruption and resumption for Human-in-the-Loop decisions.

### Pydantic

- Defined a typed shared state.
- Used safe default factories for lists and dictionaries.
- Preserved compatibility with dictionary-based agent code.

### MCP

- Standardized communication with weather and budget tools.
- Separated external tool logic from agent reasoning.
- Kept tool execution predictable through dedicated nodes.

### Long-Term Memory

- Stored trips, preferences, and chats in SQLite.
- Isolated data using `user_id`.
- Reloaded memory during login and graph execution.

### UI/UX

- Removed the fixed input bar.
- Improved contrast and widget visibility.
- Added workflow progress, memory, and Human Review panels.

---

## 🔬 Exploration

### Workflow Routing

- Explored conditional graph paths.
- Added early stopping for missing details.
- Routed over-budget plans to Human Review.

### Replanning

- Tested activity, transport, and dining cost reductions.
- Preserved essential experiences while controlling costs.
- Displayed revised estimates and savings.

### Persistent Memory

- Compared separate databases with user-separated records.
- Selected a single database with `user_id` filtering.
- Added chat and preference persistence.

### Human Approval

- Identified budget decisions as a high-impact review point.
- Explored graph checkpoints and resumable execution.
- Supported multiple user-controlled outcomes.

### UI Synchronization

- Connected SQLite data to Pydantic state and Streamlit state.
- Added explicit refresh and rerun behavior.
- Resolved stale sidebar and widget-state issues.

---

## 🔮 Future Enhancements

- Replace SQLite with PostgreSQL for larger deployments.
- Use a durable LangGraph checkpoint backend.
- Add Microsoft Entra ID or OAuth authentication.
- Use bcrypt or Argon2 for password hashing.
- Add semantic memory with embeddings and vector search.
- Add hotel, flight, map, and booking integrations.
- Add itinerary export to PDF or calendar.
- Add administrator monitoring and usage analytics.
- Separate the frontend and backend using Streamlit or React with FastAPI.
- Deploy using Azure, Docker, or another cloud platform.

---

## 🤝 Contribution Workflow

Create a feature branch:

```powershell
git checkout -b feature/your-feature-name
```

Stage and commit changes:

```powershell
git add .
git commit -m "Add your feature description"
```

Push the branch:

```powershell
git push -u origin feature/your-feature-name
```

Then create a pull request into the main branch.

---

## 👨‍💻 Author

**Abhijeet Kumar**  
AI/ML and Agentic AI Project

---

## 📄 License

This project is intended for educational, demonstration, and portfolio purposes.

If the repository will be distributed publicly, add a suitable license file such as the MIT License and update this section accordingly.
