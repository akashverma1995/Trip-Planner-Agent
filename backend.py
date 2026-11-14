import os
import sys
import uuid
import certifi
import operator
from pathlib import Path
from typing import TypedDict, Annotated, Optional, Dict, Any
from dotenv import load_dotenv

# Ensure parent directory is in sys.path
_parent_dir = str(Path(__file__).resolve().parent)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

load_dotenv()

# Configure SSL certificates
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

import psycopg
from psycopg.rows import dict_row

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)
from langchain_groq import ChatGroq

from tools.tavily_tool import tavily_search, tavily_search_async
from tools.flight_tool import search_flights, search_flights_async


# ==============================================================================
# 1. Configuration & Resilient LLM Setup
# ==============================================================================

def get_database_url() -> Optional[str]:
    """Retrieve and format database URL with required SSL parameters."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return None

    if "sslmode=" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url = f"{database_url}{separator}sslmode=require"

    return database_url


GROQ_API_KEY = (os.getenv("GROQ_API_KEY") or "").strip().strip('"').strip("'")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "2500"))

# Resilient LLM configuration with timeout, retries, and expanded output capacity
llm = ChatGroq(
    model=LLM_MODEL,
    api_key=GROQ_API_KEY or "dummy_key",
    temperature=0.3,
    max_retries=2,
    timeout=90,
    max_tokens=MAX_OUTPUT_TOKENS,
)


# ==============================================================================
# 2. State Definition (Typed Contracts & Additive Reducers)
# ==============================================================================

class TravelState(TypedDict):
    """
    Central state container for the LangGraph travel pipeline.
    Uses operator.add on messages and llm_calls to prevent race conditions during parallel execution.
    """
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    flight_results: str
    hotel_results: str
    itinerary: str
    final_response: str
    llm_calls: Annotated[int, operator.add]


# ==============================================================================
# 3. Agent Node Functions (Single Responsibility)
# ==============================================================================

def flight_agent(state: TravelState) -> Dict[str, Any]:
    """
    Flight Agent: Searches live flights using the cached FlightService.
    Can execute in parallel with hotel_agent.
    """
    query = state.get("user_query", "")
    flight_data = search_flights(query)

    return {
        "flight_results": flight_data,
        "messages": [AIMessage(content="Flight information fetched.")],
        "llm_calls": 0,  # Tool call, no LLM tokens used
    }


async def flight_agent_async(state: TravelState) -> Dict[str, Any]:
    """Asynchronous flight search for non-blocking FastAPI execution."""
    query = state.get("user_query", "")
    flight_data = await search_flights_async(query)

    return {
        "flight_results": flight_data,
        "messages": [AIMessage(content="Flight information fetched.")],
        "llm_calls": 0,
    }


def hotel_agent(state: TravelState) -> Dict[str, Any]:
    """
    Hotel Agent: Queries accommodations using the cached TavilyService.
    Can execute in parallel with flight_agent.
    """
    query = f"Best hotels and accommodations for {state.get('user_query', '')}"
    hotel_data = tavily_search(query)

    return {
        "hotel_results": hotel_data,
        "messages": [AIMessage(content="Hotel information fetched.")],
        "llm_calls": 0,
    }


async def hotel_agent_async(state: TravelState) -> Dict[str, Any]:
    """Asynchronous hotel search for non-blocking FastAPI execution."""
    query = f"Best hotels and accommodations for {state.get('user_query', '')}"
    hotel_data = await tavily_search_async(query)

    return {
        "hotel_results": hotel_data,
        "messages": [AIMessage(content="Hotel information fetched.")],
        "llm_calls": 0,
    }


def planner_agent(state: TravelState) -> Dict[str, Any]:
    """
    Unified Planning Agent: Synthesizes flights and hotels into a complete,
    practical, and beautifully structured travel plan in a single LLM invocation.
    Guarantees full completion of all 6 sections including Day-by-Day itinerary and budget.
    """
    prompt = f"""
You are a professional AI travel booking assistant. Using the provided live flight and hotel data, generate a complete, thorough, and actionable travel plan.

User Request:
{state.get('user_query', '')}

Flight Information:
{state.get('flight_results', 'No flights found')}

Hotel Information:
{state.get('hotel_results', 'No hotels found')}

CRITICAL INSTRUCTIONS:
You MUST generate ALL 6 of the following sections in full. Do NOT truncate or omit any section.

### 1. Trip Summary
Brief destination overview, best time to visit, and highlights of the trip.

### 2. Flight Options
Highlight the top 2-3 most convenient flight options from the data (Airlines, Flight Numbers, Departure/Arrival timings). Mention booking directly on airline sites if live fares are not shown.

### 3. Recommended Accommodations
Highlight the top 3 hotel/stay options from the search results with location benefits and amenities.

### 4. Day-by-Day Itinerary
Provide a complete, detailed schedule for EVERY single day of the requested duration (e.g., Day 1, Day 2, Day 3, ...).
For each day, structure by:
- **Morning**: Main attraction/activity
- **Afternoon**: Exploration & lunch spot
- **Evening**: Leisure, dinner, or nightlife

### 5. Estimated Budget Breakdown
Provide an itemized cost estimate in the local currency or USD:
- Flights: Estimated cost
- Accommodation: Estimated nightly & total cost
- Food & Dining: Daily estimate
- Local Transport & Sightseeing: Daily estimate
- **Total Estimated Trip Cost**: Sum total with budget vs luxury range

### 6. Essential Travel Tips & Recommendations
Key packing tips, local transport hacks (metro/cabs), cultural etiquette, and safety advice.
"""
    response = llm.invoke([
        SystemMessage(content="You are an expert AI travel assistant specializing in exhaustive, high-quality, practical travel itineraries. Always complete all 6 sections."),
        HumanMessage(content=prompt)
    ])

    return {
        "itinerary": response.content,
        "final_response": response.content,
        "messages": [response],
        "llm_calls": 1,
    }


async def planner_agent_async(state: TravelState) -> Dict[str, Any]:
    """Asynchronous unified planning agent."""
    prompt = f"""
You are a professional AI travel booking assistant. Using the provided live flight and hotel data, generate a complete, thorough, and actionable travel plan.

User Request:
{state.get('user_query', '')}

Flight Information:
{state.get('flight_results', 'No flights found')}

Hotel Information:
{state.get('hotel_results', 'No hotels found')}

CRITICAL INSTRUCTIONS:
You MUST generate ALL 6 of the following sections in full. Do NOT truncate or omit any section.

### 1. Trip Summary
Brief destination overview, best time to visit, and highlights of the trip.

### 2. Flight Options
Highlight the top 2-3 most convenient flight options from the data (Airlines, Flight Numbers, Departure/Arrival timings). Mention booking directly on airline sites if live fares are not shown.

### 3. Recommended Accommodations
Highlight the top 3 hotel/stay options from the search results with location benefits and amenities.

### 4. Day-by-Day Itinerary
Provide a complete, detailed schedule for EVERY single day of the requested duration (e.g., Day 1, Day 2, Day 3, ...).
For each day, structure by:
- **Morning**: Main attraction/activity
- **Afternoon**: Exploration & lunch spot
- **Evening**: Leisure, dinner, or nightlife

### 5. Estimated Budget Breakdown
Provide an itemized cost estimate in the local currency or USD:
- Flights: Estimated cost
- Accommodation: Estimated nightly & total cost
- Food & Dining: Daily estimate
- Local Transport & Sightseeing: Daily estimate
- **Total Estimated Trip Cost**: Sum total with budget vs luxury range

### 6. Essential Travel Tips & Recommendations
Key packing tips, local transport hacks (metro/cabs), cultural etiquette, and safety advice.
"""
    response = await llm.ainvoke([
        SystemMessage(content="You are an expert AI travel assistant specializing in exhaustive, high-quality, practical travel itineraries. Always complete all 6 sections."),
        HumanMessage(content=prompt)
    ])

    return {
        "itinerary": response.content,
        "final_response": response.content,
        "messages": [response],
        "llm_calls": 1,
    }

    return {
        "itinerary": response.content,
        "final_response": response.content,
        "messages": [response],
        "llm_calls": 1,
    }


# ==============================================================================
# 4. Graph Construction (Parallel Fan-Out / Fan-In)
# ==============================================================================

def build_travel_graph() -> StateGraph:
    """
    Constructs the StateGraph with parallel execution of flight and hotel searches:
    
            ┌──► flight_agent ──┐
    START ──┤                   ├──► planner_agent ──► END
            └──► hotel_agent  ──┘
    """
    builder = StateGraph(TravelState)

    builder.add_node("flight_agent", flight_agent)
    builder.add_node("hotel_agent", hotel_agent)
    builder.add_node("planner_agent", planner_agent)

    # Parallel Fan-out: execute flight search and hotel search concurrently
    builder.add_edge(START, "flight_agent")
    builder.add_edge(START, "hotel_agent")

    # Fan-in: wait for both to complete before building final plan
    builder.add_edge(["flight_agent", "hotel_agent"], "planner_agent")
    builder.add_edge("planner_agent", END)

    return builder


# ==============================================================================
# 5. Resilient Checkpointer & Compilation
# ==============================================================================

def initialize_checkpointer() -> Optional[PostgresSaver]:
    """
    Safely initializes PostgreSQL checkpointer with auto-recovery.
    Falls back gracefully if database is unreachable during local testing.
    """
    db_url = get_database_url()
    if not db_url:
        print("[Notice] DATABASE_URL not configured. Running graph without PostgreSQL persistence.")
        return None

    try:
        conn = psycopg.connect(
            db_url,
            autocommit=True,
            row_factory=dict_row,
            connect_timeout=10,
        )
        saver = PostgresSaver(conn)
        saver.setup()
        return saver
    except Exception as exc:
        print(f"[Warning] PostgreSQL checkpointer connection failed: {exc}. Running without persistence.")
        return None


# Compile the graph
_graph_builder = build_travel_graph()
_checkpointer = initialize_checkpointer()

if _checkpointer:
    travel_graph = _graph_builder.compile(checkpointer=_checkpointer)
else:
    travel_graph = _graph_builder.compile()


# ==============================================================================
# 6. Public Service Layer (FastAPI & Agent Invocation)
# ==============================================================================

def run_travel_agent(user_input: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Synchronous execution endpoint for FastAPI (app.py).
    Preserves multi-turn conversation state without wiping previous checkpoints.
    """
    active_thread_id = thread_id or f"user_{uuid.uuid4().hex}"

    config = {
        "configurable": {
            "thread_id": active_thread_id
        }
    }

    # Only pass user input and message to avoid overwriting existing checkpoints
    initial_payload = {
        "messages": [HumanMessage(content=user_input)],
        "user_query": user_input,
    }

    result = travel_graph.invoke(initial_payload, config=config)

    # Extract final assistant answer
    final_answer = ""
    if result.get("final_response"):
        final_answer = result["final_response"]
    elif result.get("messages"):
        final_answer = result["messages"][-1].content

    return {
        "thread_id": active_thread_id,
        "answer": final_answer,
        "flight_results": result.get("flight_results", ""),
        "hotel_results": result.get("hotel_results", ""),
        "itinerary": result.get("itinerary", ""),
        "llm_calls": result.get("llm_calls", 0),
    }


async def run_travel_agent_async(user_input: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Non-blocking asynchronous execution endpoint for FastAPI.
    Runs the synchronous LangGraph pipeline in a dedicated worker thread,
    guaranteeing full compatibility with synchronous checkpointers (PostgresSaver).
    """
    import anyio
    return await anyio.to_thread.run_sync(run_travel_agent, user_input, thread_id)


# ==============================================================================
# 7. Local Testing Block
# ==============================================================================

if __name__ == "__main__":
    print("Testing Travel Agent Backend (Parallel LangGraph Architecture):\n")
    test_query = "Plan a 5 days trip to Goa from Mumbai"
    print(f"User Query: '{test_query}'\n")

    response = run_travel_agent(test_query)
    print("--- Execution Summary ---")
    print(f"Thread ID: {response['thread_id']}")
    print(f"LLM Calls: {response['llm_calls']}")
    print("\n--- Final Answer ---")
    print(response["answer"])


