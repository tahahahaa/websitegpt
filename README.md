# 🌐 WebsiteGPT

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Groq](https://img.shields.io/badge/Groq_AI-F55036?style=for-the-badge&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logoColor=white)
![FAISS](https://img.shields.io/badge/FAISS-0467DF?style=for-the-badge&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)

> **Paste any website URL and instantly chat with its content using AI — including JS-rendered pages, dropdowns, accordions, iFrames, and paginated tables.**


**[Live Demo →](https://websitegpt-app.streamlit.app/)**
---

## ⚡ What It Does

Paste a URL, click Load, and start asking questions. WebsiteGPT:

1. 🔍 **Scrapes the website** using Playwright + BeautifulSoup
2. 🧠 **Handles dynamic content** — JS rendering, dropdowns, accordions, iFrames, pagination
3. ✂️ **Chunks and embeds** the content using HuggingFace sentence transformers
4. 🗄️ **Indexes into FAISS** vector store for fast semantic search
5. 💬 **Answers questions** using Groq's Llama 3.1 — strictly from the website content only
6. 📄 **Cites sources** — every answer shows which page URL it came from

No hallucinations. No outside knowledge. Just your website, searchable by AI.

---

## 🔧 How It Works

```
User pastes URL
      ↓
Playwright launches headless browser
      ↓
Page fully renders (JS, dropdowns, iFrames all expanded)
      ↓
BeautifulSoup extracts clean text + tables
      ↓
Text split into chunks → embedded with HuggingFace
      ↓
Chunks stored in FAISS vector index
      ↓
User asks question → MMR retrieval finds relevant chunks
      ↓
Groq (Llama 3.1 8B) answers strictly from retrieved content
      ↓
Answer + source URLs shown in chat
```

---

## 🌍 What Sites Work

| Site Type | Works? | Notes |
|---|---|---|
| Company / About pages | ✅ | Perfect |
| Documentation sites | ✅ | Perfect |
| Blogs / News articles | ✅ | Perfect |
| FAQ pages | ✅ | Dropdowns auto-expanded |
| Paginated tables | ✅ | Each page scraped separately |
| iFrame content | ✅ | iFrame URLs followed and scraped |
| JS-rendered content | ✅ | Playwright handles full render |
| YouTube / Social media | ❌ | Login-walled or API-driven |
| Sites blocking bots | ⚠️ | Try reducing max pages to 1 |

---

## 🚀 Setup

### Step 1 — Clone and install
```bash
git clone https://github.com/tahahahaa/websitegpt.git
cd websitegpt
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### Step 2 — Add your Groq API key
Create a `.env` file:
```
GROQ_API_KEY=gsk_your_key_here
```
Get a free key at [console.groq.com](https://console.groq.com)

### Step 3 — Run
```bash
streamlit run app.py
```

---

## 🧪 Test URLs

| Type | URL |
|---|---|
| Static data | https://www.scrapethissite.com/pages/simple/ |
| Paginated table | https://www.scrapethissite.com/pages/forms/ |
| iFrames | https://www.scrapethissite.com/pages/frames/ |
| JS rendered | https://quotes.toscrape.com/js/ |
| Books catalog | https://books.toscrape.com/ |

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| UI | Streamlit |
| Scraping | Playwright + BeautifulSoup + requests |
| Embeddings | HuggingFace sentence-transformers |
| Vector Store | FAISS |
| LLM | Groq — Llama 3.1 8B Instant |
| RAG Framework | LangChain 0.3.25 |

---

## 📁 Project Structure

```
websitegpt/
├── app.py            ← Streamlit UI
├── scraper.py        ← Playwright + BS4 scraper
├── rag_engine.py     ← FAISS + LangChain QA chain
├── requirements.txt
├── .env              ← GROQ_API_KEY (not committed)
└── .gitignore
```

---



---

## 👨‍💻 Author

**Muhammad Taha Sheikh**
🐙 [GitHub](https://github.com/tahahahaa)

---

## ⚠️ Disclaimer

WebsiteGPT is designed for publicly accessible websites. Do not use it to scrape sites that prohibit scraping in their Terms of Service.

---

## ⭐ Star this repo if it helped you!
