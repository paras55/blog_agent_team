from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional
import asyncio
import time
import requests
import openai
from langchain_openai import ChatOpenAI
from browser_use import Agent, BrowserConfig, Browser
import ast

# For Medium Agent
openai_api_key_breakdown    = ""       # For task breakdown
openai_api_key_medium       = ""          # For running the Medium agent
openai_api_key_extraction   = ""      # For extracting the final output

# For Content Selector Agent
openai_api_key_content_selector = ""

# For Blog Writing Agent
openai_api_key_blog = ""

# For Perplexity Agent (used with requests)
perplexity_api_key = ""

# Assistant IDs for beta threads agents
CONTENT_SELECTOR_ASSISTANT_ID = ""
BLOG_WRITER_ASSISTANT_ID      = ""

# Chrome configuration for Medium Agent
chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
browser = Browser(config=BrowserConfig(chrome_instance_path=chrome_path))

# === Medium Output now fetched via Agent ===
async def get_medium_output() -> str:
    user_task = ('''Open up Medium, scroll through the feed until you have 10 articles and return the list of article titles.''')
    print("🚀 Running Medium Agent...")
    execution_result = await run_agent_with_retry(user_task, openai_api_key_medium)

    if execution_result:
        extraction_prompt = f"""
        You are an AI assistant analyzing the full result of a browser automation agent run.
        Given the full execution result below, extract and return only the **final output** of the agent — typically the `extracted_content` from the step where \"is_done\": true.
        Execution Result: {execution_result}
        Respond with just the final output content.
        """
        extraction_llm = ChatOpenAI(model="gpt-4o", openai_api_key=openai_api_key_extraction)
        response = extraction_llm.invoke(extraction_prompt)
        final_output = response.content.strip()
        return final_output
    else:
        return ""

async def run_agent_with_retry(task_plan: str, api_key: str, max_retries: int = 3):
    """
    Uses a dedicated API key to run the browser automation agent.
    Retries the task up to max_retries times if errors occur.
    """
    retries = 0
    while retries < max_retries:
        try:
            llm_local = ChatOpenAI(model="gpt-4o", openai_api_key=api_key)
            agent = Agent(task=task_plan, llm=llm_local, browser=browser)
            result = await agent.run()  # Capture the final output of the agent run
            await browser.close()
            return result
        except Exception as e:
            print(f"[Medium Agent Attempt {retries+1}] Task failed: {e}")
            retries += 1
    print(f"❌ Medium Agent failed after {max_retries} retries. Aborting.")
    return None

# === Blog Pipeline Functions ===
def content_selector(ideas, api_key) -> list:
    openai.api_key = api_key
    thread = openai.beta.threads.create()
    thread_id = thread.id
    print ("Here are the ideas raw", ideas)
    openai.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=[{"type": "text", "text": "\n".join(ideas)}]
    )


    run = openai.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=CONTENT_SELECTOR_ASSISTANT_ID
    )

    while True:
        run_status = openai.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        if run_status.status == "completed":
            break
        elif run_status.status == "failed":
            print("❌ Assistant run failed.")
            return []
        time.sleep(1)

    messages = openai.beta.threads.messages.list(thread_id=thread_id)
    output_list = []
    for msg in reversed(messages.data):
        if msg.role == "assistant":
            for content_block in msg.content:
                if hasattr(content_block, "text"):
                    output_list.append(content_block.text.value)
            break
    return output_list

def run_perplexity_agent(idea: str) -> str:
    url = "https://api.perplexity.ai/chat/completions"
    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": "Be precise and concise."},
            {"role": "user", "content": f"Provide in-depth research on the following topic: {idea}"}
        ],
        "max_tokens": 500,
        "temperature": 0.2,
        "top_p": 0.9,
        "return_images": False,
        "return_related_questions": False,
        "top_k": 0,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 1,
        "web_search_options": {"search_context_size": "high"}
    }
    headers = {
        "Authorization": f"Bearer {perplexity_api_key}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        print(response.text)
        return response.text
    else:
        print("❌ Error from Perplexity:", response.status_code, response.text)
        return ""

def blog_writer(research_data: str, api_key: str) -> str:
    openai.api_key = api_key
    thread = openai.beta.threads.create()
    thread_id = thread.id

    openai.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=f"Write a complete blog based on this research:\n{research_data}"
    )

    run_obj = openai.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=BLOG_WRITER_ASSISTANT_ID
    )

    while True:
        run_status = openai.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_obj.id)
        if run_status.status == "completed":
            break
        elif run_status.status == "failed":
            return ""
        time.sleep(1)

    messages = openai.beta.threads.messages.list(thread_id=thread_id)
    blog_post = ""
    for msg in reversed(messages.data):
        if msg.role == "assistant":
            for content_block in msg.content:
                if hasattr(content_block, "text"):
                    blog_post += content_block.text.value
            break
    return blog_post

async def ghost_draft(blog_post: str) -> str:
    user_task = f"Always go to https://athina-ai-hub.ghost.io/ghost/#/posts, create a new post, paste the article below in proper structured format as given to you" + blog_post
    llm_local = ChatOpenAI(model="gpt-4o", openai_api_key=openai_api_key_medium)
    agent = Agent(task=user_task, llm=llm_local, browser=browser)
    result = await agent.run()
    return result

# === Shared State ===
class BlogState(TypedDict):
    ideas: List[str]
    selected_ideas: List[str]
    current_idea: Optional[str]
    research_data: Optional[str]
    blog_post: Optional[str]
    completed_blogs: dict

# === Node Functions ===
def select_ideas(state: BlogState) -> BlogState:
    raw_selected = content_selector(state["ideas"], openai_api_key_content_selector)
    print("this is raw selected", raw_selected)

    parsed_selected = []

    if isinstance(raw_selected, str):
        try:
            parsed_selected = ast.literal_eval(raw_selected)
        except Exception as e:
            print("Error parsing selected ideas:", e)
    elif isinstance(raw_selected, list) and len(raw_selected) == 1 and isinstance(raw_selected[0], str):
        try:
            # Handles the case where it's a list with one string that looks like a list
            parsed_selected = ast.literal_eval(raw_selected[0])
        except Exception as e:
            print("Error parsing nested list string:", e)
    elif isinstance(raw_selected, list):
        parsed_selected = raw_selected

    cleaned = [item.strip().strip('`').strip() for item in parsed_selected if isinstance(item, str) and item.strip()]

    print(f"🧠 Selected ideas (cleaned): {cleaned}")
    return {**state, "selected_ideas": cleaned, "completed_blogs": {}}

def pick_next_idea(state: BlogState) -> BlogState:
    if state["selected_ideas"]:
        next_idea = state["selected_ideas"].pop(0)
        print(f"📌 Picking next idea: {next_idea}")
        return {**state, "current_idea": next_idea}
    return state

def research_agent(state: BlogState) -> BlogState:
    research = run_perplexity_agent(state["current_idea"])
    return {**state, "research_data": research}

def blog_writer_agent(state: BlogState) -> BlogState:
    blog = blog_writer(state["research_data"], openai_api_key_blog)
    return {**state, "blog_post": blog}

async def ghost_drafter_agent(state: BlogState) -> BlogState:
    await ghost_draft(state["blog_post"])  # ✅ Proper async
    updated_completed = {**state["completed_blogs"], state["current_idea"]: state["blog_post"]}
    return {
        **state,
        "blog_post": None,
        "current_idea": None,
        "research_data": None,
        "completed_blogs": updated_completed
    }

def has_more_ideas(state: BlogState) -> str:
    return "pick_next" if state["selected_ideas"] else END

# === LangGraph Definition ===
workflow = StateGraph(BlogState)
workflow.add_node("select_ideas", select_ideas)
workflow.add_node("pick_next", pick_next_idea)
workflow.add_node("research", research_agent)
workflow.add_node("write", blog_writer_agent)
workflow.add_node("draft", ghost_drafter_agent)
workflow.set_entry_point("select_ideas")
workflow.add_edge("select_ideas", "pick_next")
workflow.add_edge("pick_next", "research")
workflow.add_edge("research", "write")
workflow.add_edge("write", "draft")
workflow.add_conditional_edges("draft", has_more_ideas, {"pick_next": "pick_next", END: END})
app = workflow.compile()

# === Execute ===
if __name__ == "__main__":
    import asyncio
    medium_raw = asyncio.run(get_medium_output())
    if not medium_raw:
        print("❌ Failed to fetch Medium output. Exiting.")
        exit()

    initial_state: BlogState = {
        "ideas": medium_raw.strip().split("\n"),
        "selected_ideas": [],
        "current_idea": None,
        "research_data": None,
        "blog_post": None,
        "completed_blogs": {}
    }
    print("🚀 Launching LangGraph Blog Orchestrator...")
    app.invoke(initial_state)
