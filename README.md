# 🧠 Autonomous AI Agents for Blog Writing

This project uses a **team of AI agents** that collaborate to automatically **write and publish blog posts**. The system simulates a writer's workflow by combining GPT assistants, a web browser, and research tools to generate high-quality content and publish it as a draft on **Ghost CMS**.

Great for marketers, developers, bloggers, or anyone curious about using AI as a writing assistant — from idea generation to browser-based publishing.

---

## 🚀 What It Does

1. **Scrapes trending article ideas** from Medium using browser automation.
2. **Chooses the best ideas** using an OpenAI GPT agent.
3. **Researches the chosen topic** using the Perplexity API.
4. **Generates a full blog post** with another GPT agent.
5. **Logs into Ghost CMS** and publishes the draft using a real browser.
6. **Optional dashboard** with Streamlit for visual feedback and progress control.

---

## 📦 Requirements

- Python 3.9+
- Google Chrome
- The following Python packages (install with `pip install -r requirements.txt`):

```bash
streamlit
openai
langchain
langgraph
pydantic
playwright
selenium
beautifulsoup4
```

---

## 🔑 Setup

### API Keys

- **OpenAI API Key**
- **Perplexity API Key**
- **Assistant IDs** for the GPTs you set up in OpenAI

### Browser Path

Set your local Chrome path in `blog_pipeline.py`:

```python
chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
```

### Ghost CMS Credentials

Ghost admin must be accessible at:

```
https://your-site.ghost.io/ghost
```

### Optional

Store your API keys in a `.env` file and load them using:

```python
import os
os.environ.get("OPENAI_API_KEY")
```

---

## 🧪 Run the Project

### CLI Mode

```bash
python blog_pipeline.py
```

This will:

- Scrape titles
- Pick one
- Research
- Write
- Log into Ghost CMS and publish

### Streamlit Dashboard

```bash
streamlit run dashboard.py
```

You'll get an interactive dashboard to monitor agent activity and blog content at each step.

---

## 📁 Project Structure

```
.
├── blog_pipeline.py       # Main pipeline with agent collaboration
├── dashboard.py           # Optional Streamlit UI
├── browser_use.py         # Ghost CMS login and post logic
├── requirements.txt       # Python dependencies
```

---

## 🧠 How It Works

Agents communicate by passing messages and memory between each step:

- 🧠 **Idea Agent** filters scraped titles.
- 🔍 **Research Agent** uses Perplexity for gathering facts and structure.
- ✍️ **Writing Agent** builds a complete blog using research and structure.
- 🌐 **Publishing Agent** opens Chrome and uploads it to Ghost CMS.
- 📊 Logs and states are displayed in the Streamlit dashboard for visibility.

---

## 🧰 Tech Stack

- **GPT Assistants API** from OpenAI
- **Perplexity API** for real-time search-based knowledge
- **Playwright or Selenium** for browser control
- **Streamlit** for visual UI
- **Ghost CMS** for final publishing

---

## 🙌 Contributing

Ideas, bug fixes, and PRs are welcome!  
Open an issue or fork the project to help expand this multi-agent publishing pipeline.

---

## ⚠️ Disclaimer

This project uses AI to generate content and automate browser actions.  
**Always review and edit generated content before publishing.**
