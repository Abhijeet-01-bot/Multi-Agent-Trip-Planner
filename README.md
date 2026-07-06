# ✈️ Multi-Agent Smart Trip Planning Assistant

A smart AI-powered trip planning assistant built using **LangGraph**, **Gemini**, **Streamlit**, and **MCP (Model Context Protocol)**.  
The system takes a natural language travel request and generates a structured, weather-aware, budget-conscious, and day-wise travel itinerary using multiple specialized agents.

---

## 📌 Project Overview

The **Multi-Agent Smart Trip Planning Assistant** helps users plan trips by understanding their travel requirements and coordinating multiple AI agents.

Example user query:

```text
Plan a trip to Goa from 10 July 2026 to 14 July 2026 for a couple with budget 400000 INR


User
 |
 v
Streamlit UI (app.py)
 |
 v
LangGraph Workflow
 |
 |--> Planner Agent
 |
 |--> Weather Agent
 |       |
 |       v
 |    MCP Client
 |       |
 |       v
 |    Weather MCP Server
 |       |
 |       v
 |    OpenWeather API
 |
 |--> Destination Agent
 |
 |--> Transport Agent
 |       |
 |       v
 |    Distance Tool
 |
 |--> Budget Agent
 |       |
 |       v
 |    MCP Client
 |       |
 |       v
 |    Budget MCP Server
 |
 |--> Replanner Agent
 |
 |--> Itinerary Composer Agent
 |
 v
Final Trip Plan
