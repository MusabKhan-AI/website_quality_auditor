# AI-Assisted Website Quality Auditor for Digital Marketing Websites

**SDC Internship — Week 2 Individual Project | Member 6**  
**Author:** Muhammad Musab Khan  
**Primary Technology Demonstrated:** Vector Database using FAISS (RAG Pipeline) & Interactive Web UI (Gradio)

---

## 1. Overview
This project is an automated Python tool that audits authorized Digital Marketing and Tech websites. It combines **deterministic HTML extraction** (BeautifulSoup) for factual signals (forms, emails, CTAs, social links) with an **AI/LLM judgment layer** grounded via a **FAISS Vector Database** (Retrieval-Augmented Generation).

---

## 2. Architecture & RAG Pipeline

```text
[Target URLs / Custom Input] ──► [HTTP Fetcher] ──► [BeautifulSoup Parser] ──► [Fact Extraction]
                                                             │
                                                             ▼
                                                    [Text Chunking]
                                                             │
                                                             ▼
                                                 [SentenceTransformers]
                                                             │
                                                             ▼
                                                   [FAISS Vector DB]
                                                             │
                                                     (Top-k Retrieval)
                                                             │
                                                             ▼
                                         [Groq LLM (Llama 3.1)] ──► [Structured Table Output]
```

### How FAISS is Used:
1. Visible webpage text is split into ~120-word chunks.
2. Chunks are converted into 384-dimensional vector embeddings using `all-MiniLM-L6-v2`.
3. Vectors are indexed into a FAISS `IndexFlatL2` database.
4. When audit questions are queried (e.g., *"What contact options exist?"*), FAISS performs L2 distance semantic search to retrieve the most relevant page context.
5. Retrieved context is sent to the LLM to generate an evidence-grounded score (0–100) and recommendations without hallucinating missing data.

---

## 3. Key Features
- **Separation of Fact & Judgment:** Facts are generated purely by code; AI only provides judgment based on retrieved evidence.
- **Interactive Web Interface (V2.0):** Real-time URL input and instant table rendering powered by Gradio.
- **Robust Error Handling:** Network timeouts, HTTP errors (403/404/429), or missing API keys fall back gracefully without crashing batch runs.
- **Multi-Format Export:** Generates report outputs in **Markdown (`audit_report.md`)**, **JSON (`audit_report.json`)**, and **CSV (`audit_report.csv`)**.

---

## 4. Version 2.0 Update: Interactive Web Application (Gradio UI)

### Upgrade Summary
In Version 1.0, the tool processed a static list of pre-configured URLs from code[cite: 5, 6]. In Version 2.0, an interactive web application layer was introduced using **Gradio**, enabling real-time custom URL analysis and instant structured table output directly inside the Google Colab environment.

### Key Improvements in V2.0:
* **Dynamic Input:** Users can input any public website URL dynamically via an input box instead of hardcoding array lists.
* **Live Table Rendering:** Outputs are immediately formatted and rendered into an interactive data table.
* **Zero-Configuration Deployment:** Runs natively within Google Colab using Gradio inline embedding, bypassing external proxy and tunnel authentication issues.

---

## 5. Setup & Running Instructions

### Version 1.0 (Batch Scripting in Google Colab):
1. Open Google Colab and paste the code from `website_quality_auditor_single_cell.py`.
2. Open the **Secrets panel (🔑 icon)** on the left sidebar in Colab[cite: 6].
3. Add a secret named `GROQ_API_KEY`, paste your Groq API key, and toggle **Notebook access** to ON.
4. Run the code cell (Shift + Enter).
5. Download the generated `audit_report.md`, `audit_report.json`, and `audit_report.csv` files from the Files panel.

### Version 2.0 (Interactive Gradio Interface):
1. Install dependencies: `!pip install gradio requests beautifulsoup4 lxml pandas numpy faiss-cpu sentence-transformers groq`.
2. Run the Gradio interface code cell[cite: 6].
3. Enter any website URL (e.g., `https://www.stripe.com`) directly into the input box.
4. Click **Submit** to view the real-time structured quality audit table rendered inline.

---

## 6. Repository Structure
```text
├── website_quality_auditor.ipynb   # Google Colab Notebook (Batch + Gradio UI)
├── README.md                       # Complete Project Documentation
├── requirements.txt                # Python Dependencies
├── audit_report.md                 # Complete Markdown Quality Report
└── audit_report.csv                # Structured CSV Export
```
---

## 7. Author
**Muhammad Musab Khan**  
BS Artificial Intelligence | SDC Internship Week 2 - Member 6