# ============================================================================
# AI-ASSISTED WEBSITE QUALITY AUDITOR — SDC INTERNSHIP WEEK 2 (Member 6)
# Run this ENTIRE cell in a single Google Colab code cell.
# ============================================================================
# WHAT THIS CELL DOES (high level):
#   1. Fetches 3-5 public website homepages safely (handles errors/timeouts).
#   2. Extracts FACTS with plain Python/BeautifulSoup (deterministic, no AI).
#   3. Cleans + chunks the page text.
#   4. Generates embeddings (sentence-transformers) for the chunks.
#   5. Stores the embeddings in a FAISS vector index + a metadata table.
#   6. Runs semantic (RAG-style) retrieval queries against FAISS.
#   7. Sends FACTS + retrieved chunks to an LLM (Groq) for JUDGMENT ONLY.
#   8. Validates the LLM's JSON, scores 0-100, and builds a final report
#      (Markdown + JSON + CSV) that clearly separates FACT vs AI JUDGMENT.
#
# Every "AI-generated" value is explicitly labeled. Nothing about facts is
# invented by the AI — if data can't be determined, we say so explicitly.
# ============================================================================

# ---------------------------------------------------------------------------
# PART A — INSTALL DEPENDENCIES (Colab only; safe to re-run)
# ---------------------------------------------------------------------------
import subprocess, sys
def _pip_install(pkgs):
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", *pkgs])

_pip_install([
    "requests", "beautifulsoup4", "lxml", "pandas", "numpy",
    "faiss-cpu", "sentence-transformers", "groq"
])

# ---------------------------------------------------------------------------
# PART B — IMPORTS
# ---------------------------------------------------------------------------
import os, re, json, time, csv, math
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from datetime import datetime
import faiss
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# PART C — CONFIGURATION (edit these as needed)
# ---------------------------------------------------------------------------
# ---- 1. Enter your 3-5 PUBLIC, AUTHORIZED website URLs here ----
WEBSITE_URLS = [
    "https://example.com",
    "https://www.wordpress.com",
    "https://www.mailchimp.com",
]

# ---- 2. Crawl / request limits (kept small & safe on purpose) ----
REQUEST_TIMEOUT_SECONDS = 10
MAX_RETRIES = 2
RETRY_BACKOFF_SECONDS = 2
MAX_INTERNAL_LINKS_TO_COUNT = 60      # cap so we don't "count forever"
USER_AGENT = "SDC-Week2-Website-Auditor/1.0 (educational project)"

# ---- 3. Chunking ----
CHUNK_MAX_WORDS = 120
CHUNK_MIN_WORDS = 15

# ---- 4. Embedding model ----
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384  # native output size of all-MiniLM-L6-v2

# ---- 5. FAISS retrieval ----
TOP_K = 4

# ---- 6. CTA keywords (configurable) ----
CTA_KEYWORDS = [
    "contact", "get started", "book", "schedule", "request",
    "free consultation", "learn more", "call", "buy", "start",
    "quote", "demo", "sign up", "subscribe", "try free"
]

# ---- 7. Social domains recognized as real social presence ----
SOCIAL_DOMAINS = [
    "facebook.com", "instagram.com", "linkedin.com", "youtube.com",
    "twitter.com", "x.com", "tiktok.com"
]

# ---- 8. LLM configuration (Groq) ----
# The provider/model can be swapped easily by changing these two lines.
LLM_PROVIDER = "groq"
LLM_MODEL = "llama-3.1-8b-instant"

def get_api_key():
    """
    Securely fetch the Groq API key.
    Priority: Colab secret named 'GROQ_API_KEY' -> environment variable.
    NEVER hard-code the key in this file.
    In Colab: click the key icon (Secrets) on the left sidebar, add
    a secret named GROQ_API_KEY, paste your key, and toggle "Notebook access".
    """
    try:
        from google.colab import userdata  # type: ignore
        key = userdata.get("GROQ_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("GROQ_API_KEY")

GROQ_API_KEY = get_api_key()

# ---------------------------------------------------------------------------
# PART D — URL VALIDATION
# ---------------------------------------------------------------------------
def validate_url(url: str):
    """Return (is_valid, normalized_url_or_error_message)."""
    if not url or not url.strip():
        return False, "Empty URL provided."
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    parsed = urlparse(url)
    if not parsed.netloc:
        return False, f"'{url}' is not a valid URL (missing domain)."
    return True, url

# ---------------------------------------------------------------------------
# PART E — SAFE HTTP FETCHING (retries, timeouts, error classification)
# ---------------------------------------------------------------------------
def safe_fetch(url: str):
    """
    Attempts to fetch a public homepage safely.
    Returns dict: {success, html, status_code, error, elapsed_seconds}
    Never raises — all failure modes are caught and reported.
    """
    headers = {"User-Agent": USER_AGENT}
    last_error = None
    for attempt in range(1, MAX_RETRIES + 2):  # first try + retries
        start = time.time()
        try:
            resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
            elapsed = round(time.time() - start, 2)
            if resp.status_code == 200 and resp.text:
                return {"success": True, "html": resp.text, "status_code": 200,
                        "error": None, "elapsed_seconds": elapsed}
            elif resp.status_code == 403:
                return {"success": False, "html": None, "status_code": 403,
                        "error": "Website blocked automated access (HTTP 403 Forbidden).",
                        "elapsed_seconds": elapsed}
            elif resp.status_code == 404:
                return {"success": False, "html": None, "status_code": 404,
                        "error": "Page not found (HTTP 404).", "elapsed_seconds": elapsed}
            elif resp.status_code == 429:
                return {"success": False, "html": None, "status_code": 429,
                        "error": "Rate limited by website (HTTP 429 Too Many Requests).",
                        "elapsed_seconds": elapsed}
            elif resp.status_code >= 500:
                last_error = f"Server error (HTTP {resp.status_code})."
            else:
                return {"success": False, "html": None, "status_code": resp.status_code,
                        "error": f"Unexpected HTTP status {resp.status_code}.",
                        "elapsed_seconds": elapsed}
        except requests.exceptions.Timeout:
            last_error = "Request timed out."
        except requests.exceptions.ConnectionError:
            last_error = "Connection error (site unreachable or DNS failure)."
        except requests.exceptions.RequestException as e:
            last_error = f"Request failed: {e}"

        if attempt <= MAX_RETRIES:
            time.sleep(RETRY_BACKOFF_SECONDS)

    return {"success": False, "html": None, "status_code": None,
            "error": last_error or "Unknown fetch error.", "elapsed_seconds": None}

# ---------------------------------------------------------------------------
# PART F — HTML PARSING / FACT EXTRACTION (deterministic, no AI)
# ---------------------------------------------------------------------------
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_REGEX = re.compile(r"(\+?\d{1,3}[\s.-]?)?(\(?\d{2,4}\)?[\s.-]?){2,4}\d{3,4}")

def extract_visible_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def extract_internal_links(soup: BeautifulSoup, base_url: str):
    domain = urlparse(base_url).netloc
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
            continue
        full = urljoin(base_url, href)
        if urlparse(full).netloc == domain:
            links.add(full)
        if len(links) >= MAX_INTERNAL_LINKS_TO_COUNT:
            break
    return sorted(links)

def detect_contact_info(soup: BeautifulSoup, text: str):
    emails = sorted(set(EMAIL_REGEX.findall(text)))
    # very rough phone heuristic; used only as a weak signal
    phone_candidates = PHONE_REGEX.findall(text)
    has_phone_like_pattern = len("".join([p for tup in phone_candidates for p in tup])) > 0 and \
        bool(re.search(r"\d{3}[\s.-]?\d{3,4}[\s.-]?\d{3,4}", text))
    contact_links = [a["href"] for a in soup.find_all("a", href=True)
                      if re.search(r"contact|about", a["href"], re.I)
                      or re.search(r"contact|about", a.get_text(), re.I)]
    address_terms = bool(re.search(r"\b(street|st\.|avenue|ave\.|road|rd\.|suite|floor|city|zip|postal)\b", text, re.I))
    return {
        "emails_found": emails[:5],
        "phone_pattern_detected": has_phone_like_pattern,
        "contact_or_about_link_found": len(contact_links) > 0,
        "address_related_terms_found": address_terms,
    }

def detect_contact_form(soup: BeautifulSoup):
    forms = soup.find_all("form")
    has_relevant_form = False
    for f in forms:
        inputs = f.find_all(["input", "textarea", "button"])
        if len(inputs) >= 2:
            has_relevant_form = True
            break
    return {"form_tag_count": len(forms), "likely_contact_form_detected": has_relevant_form}

def detect_social_links(soup: BeautifulSoup):
    found = {}
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        for domain in SOCIAL_DOMAINS:
            if domain in href:
                found.setdefault(domain, href)
    return found  # dict of domain -> first matching URL (empty if none)

def detect_cta_buttons(soup: BeautifulSoup):
    matches = []
    for el in soup.find_all(["a", "button"]):
        label = el.get_text(strip=True).lower()
        if not label:
            continue
        for kw in CTA_KEYWORDS:
            if kw in label:
                matches.append(el.get_text(strip=True))
                break
    return sorted(set(matches))[:20]

def detect_navigation_links(soup: BeautifulSoup):
    nav_tags = soup.find_all(["nav"])
    nav_link_count = 0
    for nav in nav_tags:
        nav_link_count += len(nav.find_all("a", href=True))
    # fallback: header-based menus if no <nav>
    if nav_link_count == 0:
        header = soup.find("header")
        if header:
            nav_link_count = len(header.find_all("a", href=True))
    return {"nav_element_count": len(nav_tags), "nav_link_count": nav_link_count}

def detect_mobile_indicators(soup: BeautifulSoup, html: str):
    viewport = soup.find("meta", attrs={"name": "viewport"})
    has_viewport = viewport is not None
    responsive_css_hint = bool(re.search(r"media\s*=\s*[\"']?\s*\(max-width|@media", html, re.I))
    return {
        "viewport_meta_tag_present": has_viewport,
        "responsive_css_reference_found": responsive_css_hint,
        "note": "These are BASIC indicators only — NOT a full mobile-responsiveness test."
    }

def extract_facts(url: str, html: str):
    soup = BeautifulSoup(html, "lxml")
    text = extract_visible_text(soup)
    title = soup.title.get_text(strip=True) if soup.title else "Not determinable from the available public page data."
    headings = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2"]) if h.get_text(strip=True)][:10]

    internal_links = extract_internal_links(soup, url)
    contact_info = detect_contact_info(soup, text)
    contact_form = detect_contact_form(soup)
    social_links = detect_social_links(soup)
    cta_buttons = detect_cta_buttons(soup)
    nav_info = detect_navigation_links(soup)
    mobile_info = detect_mobile_indicators(soup, html)

    return {
        "title": title,
        "headings": headings,
        "visible_text": text,
        "word_count": len(text.split()),
        "discoverable_internal_links_count": len(internal_links),
        "discoverable_internal_links_note": (
            "Discoverable internal links/pages found from the analyzed homepage only "
            f"(capped at {MAX_INTERNAL_LINKS_TO_COUNT}). This is NOT the total page count of the site."
        ),
        "internal_links_sample": internal_links[:10],
        "contact_info": contact_info,
        "contact_form": contact_form,
        "social_links_found": social_links,
        "cta_buttons_found": cta_buttons,
        "navigation": nav_info,
        "mobile_indicators": mobile_info,
    }

# ---------------------------------------------------------------------------
# PART G — TEXT CHUNKING
# ---------------------------------------------------------------------------
def build_chunks(url: str, facts: dict):
    """
    Splits page content into small, meaningful chunks for embedding.
    Why chunk? Embedding models work best on short, focused text; FAISS
    retrieval is more accurate when it can pinpoint a specific chunk
    (e.g. a heading or paragraph) instead of matching an entire page.
    """
    chunks = []
    idx = 0

    def add_chunk(chunk_text, content_type):
        nonlocal idx
        chunk_text = chunk_text.strip()
        if len(chunk_text.split()) < CHUNK_MIN_WORDS and content_type not in ("title", "heading"):
            return
        if not chunk_text:
            return
        idx += 1
        chunks.append({
            "chunk_id": f"{urlparse(url).netloc}-{idx}",
            "url": url,
            "content_type": content_type,
            "text": chunk_text[:1000],
        })

    if facts["title"]:
        add_chunk(f"Page title: {facts['title']}", "title")
    for h in facts["headings"]:
        add_chunk(f"Heading: {h}", "heading")

    # split visible text into word-bounded chunks
    words = facts["visible_text"].split()
    for i in range(0, len(words), CHUNK_MAX_WORDS):
        piece = " ".join(words[i:i + CHUNK_MAX_WORDS])
        add_chunk(piece, "body_text")

    return chunks

# ---------------------------------------------------------------------------
# PART H — EMBEDDINGS
# ---------------------------------------------------------------------------
print("Loading embedding model (all-MiniLM-L6-v2)... this runs once.")
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

def embed_texts(texts):
    """Returns a float32 numpy array of shape (n_texts, EMBEDDING_DIM)."""
    if not texts:
        return np.zeros((0, EMBEDDING_DIM), dtype="float32")
    vectors = embedding_model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return vectors.astype("float32")

# ---------------------------------------------------------------------------
# PART I — FAISS VECTOR DATABASE
# ---------------------------------------------------------------------------
# We use IndexFlatL2: a simple brute-force L2 (Euclidean distance) index.
# Why IndexFlatL2 for THIS project? Our dataset is tiny (a few hundred
# chunks from 3-5 pages), so brute-force search is fast and exact —
# no need for the approximate indexes (IVF/HNSW) that large-scale FAISS
# deployments use. It's also the easiest index type to understand as a
# beginner: it just measures straight-line distance between vectors.
#
# IMPORTANT: FAISS only stores VECTORS + their integer position.
# It does NOT store the original text. We keep a separate Python list
# ("metadata_store") that maps each vector's position back to the real
# chunk text, URL, and chunk_id. This is the standard FAISS + metadata
# pattern used in real RAG systems.

faiss_index = faiss.IndexFlatL2(EMBEDDING_DIM)
metadata_store = []  # list of dicts, position i corresponds to vector i

def add_chunks_to_faiss(chunks):
    if not chunks:
        return
    texts = [c["text"] for c in chunks]
    vectors = embed_texts(texts)
    faiss_index.add(vectors)
    metadata_store.extend(chunks)

def faiss_search(query: str, top_k: int = TOP_K, url_filter: str = None):
    """
    Embeds the query, searches FAISS for the top_k nearest chunks,
    and returns the matching metadata (text + source info).
    top_k = "how many of the closest matches to return".
    """
    if faiss_index.ntotal == 0:
        return []
    query_vector = embed_texts([query])
    # search more than top_k so we can filter by URL if needed
    search_k = min(faiss_index.ntotal, top_k * 5 if url_filter else top_k)
    distances, indices = faiss_index.search(query_vector, search_k)
    results = []
    for dist, pos in zip(distances[0], indices[0]):
        if pos == -1:
            continue
        meta = metadata_store[pos]
        if url_filter and meta["url"] != url_filter:
            continue
        results.append({**meta, "distance": float(dist)})
        if len(results) >= top_k:
            break
    return results

# ---------------------------------------------------------------------------
# PART J — LLM PROMPTS (Version 1 and Version 2 / improved)
# ---------------------------------------------------------------------------
AUDIT_QUERIES = [
    "What services does this business offer?",
    "What contact and lead generation options exist?",
    "What trust signals are present?",
    "What calls to action exist?",
    "What important business information is missing?",
    "What social presence is visible?",
]

def build_prompt_v1(url, facts, retrieved_chunks):
    """PROMPT VERSION 1 — initial, simpler instructions."""
    return f"""You are auditing the website: {url}

FACTS (already detected by code, treat as ground truth):
{json.dumps(facts, indent=2)[:3000]}

RELEVANT PAGE CONTENT (retrieved via vector search):
{json.dumps([c['text'] for c in retrieved_chunks], indent=2)[:2500]}

Rate this website's quality from 0-100 and list problems, missing features,
recommendations, and a priority (High/Medium/Low).
Return ONLY JSON in this exact shape:
{{"score": 0, "problems": [], "missing_features": [], "recommendations": [], "priority": "Low"}}
"""

def build_prompt_v2(url, facts, retrieved_chunks):
    """
    PROMPT VERSION 2 — IMPROVED after manual review.
    Changes made vs V1 (see PART 16 in the write-up for full explanation):
      1. Explicitly forbids inventing facts not present in FACTS/CONTENT.
      2. Requires citing WHICH fact/evidence supports each problem.
      3. Gives explicit scoring weights so scores are more consistent/grounded.
      4. Requires "Not determinable from the available public page data."
         wording whenever evidence is missing, instead of guessing.
    """
    return f"""You are a careful website quality auditor. You must base your judgment
ONLY on the FACTS and RETRIEVED CONTENT below. Do NOT invent information.
If something cannot be determined from this data, explicitly write:
"Not determinable from the available public page data."

WEBSITE: {url}

[FACT — AUTOMATICALLY DETECTED]
{json.dumps(facts, indent=2)[:3000]}

[RETRIEVED EVIDENCE — TOP MATCHING CONTENT CHUNKS]
{json.dumps([c['text'] for c in retrieved_chunks], indent=2)[:2500]}

SCORING GUIDANCE (weight roughly like this out of 100):
  - Completeness of business info & content clarity: 20
  - Contact / lead-generation functionality (form, email, phone): 20
  - Calls-to-action presence & clarity: 15
  - Trust signals (about/contact pages, professional content): 15
  - Social presence: 10
  - Basic mobile/responsive indicators: 10
  - Navigation & discoverability: 10

RULES:
  - Every "problem" you list must be traceable to a specific fact or
    piece of retrieved evidence above — do not speculate beyond it.
  - Do not claim mobile-responsiveness is "confirmed" — only basic
    indicators were checked.
  - priority must be one of: "High", "Medium", "Low".
  - score must be an integer 0-100.

Return ONLY valid JSON, no extra text, in exactly this shape:
{{"score": 0, "problems": [], "missing_features": [], "recommendations": [], "priority": "Low"}}
"""

# Use the improved prompt as the default for the main run.
ACTIVE_PROMPT_BUILDER = build_prompt_v2

# ---------------------------------------------------------------------------
# PART K — LLM CALL + JSON VALIDATION
# ---------------------------------------------------------------------------
def call_llm(prompt: str):
    """
    Calls the Groq LLM API. Returns (success, parsed_json_or_None, raw_text_or_error).
    Swap provider/model easily by editing LLM_PROVIDER / LLM_MODEL above and
    this function's client call.
    """
    if not GROQ_API_KEY:
        return False, None, "No API key configured (set GROQ_API_KEY as a Colab secret or env var)."

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a strict JSON-only API. Respond with valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=800,
        )
        raw = response.choices[0].message.content
        return True, None, raw
    except Exception as e:
        return False, None, f"LLM API call failed: {e}"

def parse_llm_json(raw_text: str):
    """
    Validates the LLM's JSON output. On failure, returns a safe fallback
    result instead of crashing, and marks it clearly as a fallback.
    """
    if not raw_text:
        return _fallback_judgment("Empty LLM response.")
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```json|^```|```$", "", cleaned, flags=re.MULTILINE).strip()
    try:
        data = json.loads(cleaned)
        score = int(data.get("score", 0))
        score = max(0, min(100, score))
        priority = data.get("priority", "Low")
        if priority not in ("High", "Medium", "Low"):
            priority = "Low"
        return {
            "score": score,
            "problems": list(data.get("problems", []))[:10],
            "missing_features": list(data.get("missing_features", []))[:10],
            "recommendations": list(data.get("recommendations", []))[:10],
            "priority": priority,
            "is_fallback": False,
        }
    except (json.JSONDecodeError, ValueError, TypeError):
        return _fallback_judgment("LLM returned invalid/non-JSON output.")

def _fallback_judgment(reason: str):
    return {
        "score": 0,
        "problems": [f"AI judgment unavailable: {reason}"],
        "missing_features": ["Not determinable from the available public page data."],
        "recommendations": ["Re-run the audit; check API key and network access."],
        "priority": "Low",
        "is_fallback": True,
    }

# ---------------------------------------------------------------------------
# PART L — PER-WEBSITE AUDIT ORCHESTRATION
# ---------------------------------------------------------------------------
def audit_website(raw_url: str):
    result = {
        "input_url": raw_url,
        "final_url": None,
        "fetch_success": False,
        "fetch_error": None,
        "facts": None,
        "retrieved_evidence": {},
        "ai_judgment": None,
    }

    is_valid, normalized = validate_url(raw_url)
    if not is_valid:
        result["fetch_error"] = normalized
        return result
    result["final_url"] = normalized

    fetch = safe_fetch(normalized)
    if not fetch["success"]:
        result["fetch_success"] = False
        result["fetch_error"] = f"Website could not be fetched. Reason: {fetch['error']}"
        return result

    result["fetch_success"] = True
    try:
        facts = extract_facts(normalized, fetch["html"])
    except Exception as e:
        result["fetch_error"] = f"HTML parsing failed: {e}"
        return result
    result["facts"] = facts

    # Chunk + embed + index this website's content
    try:
        chunks = build_chunks(normalized, facts)
        add_chunks_to_faiss(chunks)
    except Exception as e:
        result["fetch_error"] = f"Embedding/FAISS indexing failed: {e}"
        return result

    # Retrieve evidence per audit query, scoped to this website
    evidence = {}
    try:
        for q in AUDIT_QUERIES:
            hits = faiss_search(q, top_k=TOP_K, url_filter=normalized)
            evidence[q] = hits
    except Exception as e:
        evidence = {"error": f"FAISS retrieval failed: {e}"}
    result["retrieved_evidence"] = evidence

    # Flatten top evidence chunks for the prompt
    all_hits = []
    for hits in evidence.values():
        if isinstance(hits, list):
            all_hits.extend(hits)
    # de-duplicate by chunk_id, keep best (lowest distance)
    seen = {}
    for h in all_hits:
        if h["chunk_id"] not in seen or h["distance"] < seen[h["chunk_id"]]["distance"]:
            seen[h["chunk_id"]] = h
    top_evidence = sorted(seen.values(), key=lambda x: x["distance"])[:TOP_K]

    prompt = ACTIVE_PROMPT_BUILDER(normalized, facts, top_evidence)
    ok, _, raw = call_llm(prompt)
    if not ok:
        result["ai_judgment"] = _fallback_judgment(raw)
    else:
        result["ai_judgment"] = parse_llm_json(raw)

    return result

# ---------------------------------------------------------------------------
# PART M — RUN THE AUDIT FOR ALL URLS
# ---------------------------------------------------------------------------
print(f"\nAuditing {len(WEBSITE_URLS)} website(s)...\n")
audit_results = []
for u in WEBSITE_URLS:
    print(f"  -> Processing: {u}")
    try:
        audit_results.append(audit_website(u))
    except Exception as e:
        # Guarantees one bad site never stops the batch
        audit_results.append({
            "input_url": u, "final_url": u, "fetch_success": False,
            "fetch_error": f"Unexpected error, skipped: {e}",
            "facts": None, "retrieved_evidence": {}, "ai_judgment": None,
        })
print("\nDone fetching/analyzing all websites.\n")

# ---------------------------------------------------------------------------
# PART N — MARKDOWN REPORT GENERATION
# ---------------------------------------------------------------------------
def format_facts_markdown(facts):
    ci = facts["contact_info"]
    cf = facts["contact_form"]
    lines = [
        f"* Discoverable internal links/pages found: **{facts['discoverable_internal_links_count']}** "
        f"({facts['discoverable_internal_links_note']})",
        f"* Emails found: {ci['emails_found'] or 'None detected'}",
        f"* Phone-like pattern detected: {ci['phone_pattern_detected']}",
        f"* Contact/About link found: {ci['contact_or_about_link_found']}",
        f"* Address-related terms found: {ci['address_related_terms_found']}",
        f"* Contact form detected: {'Yes' if cf['likely_contact_form_detected'] else 'No'} "
        f"({cf['form_tag_count']} <form> tag(s) found)",
        f"* Social links found: {list(facts['social_links_found'].keys()) or 'None detected'}",
        f"* CTA buttons found: {facts['cta_buttons_found'] or 'None detected'}",
        f"* Navigation links found: {facts['navigation']['nav_link_count']}",
        f"* Mobile/responsive basic indicators: viewport tag = {facts['mobile_indicators']['viewport_meta_tag_present']}, "
        f"responsive CSS hint = {facts['mobile_indicators']['responsive_css_reference_found']} "
        f"({facts['mobile_indicators']['note']})",
        f"* Page word count (visible text): {facts['word_count']}",
    ]
    return "\n".join(lines)

def build_markdown_report(results):
    md = ["# AI-Assisted Website Quality Audit\n"]
    md.append("## Executive Summary\n")
    md.append(f"Number of websites analyzed: **{len(results)}**\n")
    md.append(f"Report generated: {datetime.now().isoformat(timespec='seconds')}\n")

    for i, r in enumerate(results, start=1):
        md.append(f"\n## Website {i}\n")
        md.append(f"URL: {r['input_url']}\n")

        if not r["fetch_success"]:
            md.append(f"**Website could not be fetched.** {r['fetch_error']}\n")
            continue

        md.append("### [FACT — AUTOMATICALLY DETECTED]\n")
        md.append(format_facts_markdown(r["facts"]) + "\n")

        md.append("### [AI JUDGMENT — GENERATED FROM AVAILABLE EVIDENCE]\n")
        j = r["ai_judgment"]
        if j.get("is_fallback"):
            md.append("_AI judgment fallback used — see problems below for reason._\n")
        md.append(f"Score: **{j['score']}/100**\n")
        md.append("\nProblems:\n")
        for idx, p in enumerate(j["problems"], 1):
            md.append(f"{idx}. {p}")
        md.append("\nMissing Features:\n")
        for idx, mfeat in enumerate(j["missing_features"], 1):
            md.append(f"{idx}. {mfeat}")
        md.append("\nRecommendations:\n")
        for idx, rec in enumerate(j["recommendations"], 1):
            md.append(f"{idx}. {rec}")
        md.append(f"\nPriority: **{j['priority']}**\n")

        md.append("### FAISS Retrieved Evidence\n")
        for q, hits in r["retrieved_evidence"].items():
            if not isinstance(hits, list) or not hits:
                continue
            md.append(f"*Query:* _{q}_")
            for h in hits[:TOP_K]:
                snippet = h["text"][:150].replace("\n", " ")
                md.append(f"  - (distance={h['distance']:.3f}) \"{snippet}...\"")

    md.append("\n## Manual Review\n")
    md.append("(Fill in after reviewing at least TWO AI outputs yourself — see template below.)\n")
    md.append("\n## Prompt Improvement\n")
    md.append("Version 1 vs Version 2 — see PROMPT_V1 / PROMPT_V2 explanation in the accompanying write-up.\n")
    md.append("\n## Limitations\n")
    md.append(
        "- Only the homepage is analyzed; internal-link counts are from that page only, capped, "
        "and are NOT the site's true total page count.\n"
        "- Mobile/responsive checks are basic HTML indicators only, not real device testing.\n"
        "- Contact/phone detection uses simple regex patterns and may miss or misfire.\n"
        "- The AI score is a subjective, evidence-based estimate — not an official certification.\n"
        "- Sites that block automated requests (403), rate-limit (429), or require JavaScript "
        "rendering may not be fully analyzable with this tool.\n"
    )
    return "\n".join(md)

markdown_report = build_markdown_report(audit_results)
print(markdown_report)

# ---------------------------------------------------------------------------
# PART O — JSON REPORT
# ---------------------------------------------------------------------------
json_report = {
    "generated_at": datetime.now().isoformat(timespec="seconds"),
    "websites_analyzed": len(audit_results),
    "results": audit_results,
}
with open("audit_report.json", "w") as f:
    json.dump(json_report, f, indent=2, default=str)

# ---------------------------------------------------------------------------
# PART P — CSV REPORT
# ---------------------------------------------------------------------------
csv_rows = []
for r in audit_results:
    if not r["fetch_success"]:
        csv_rows.append({
            "Website": r["input_url"], "Score": "", "Priority": "",
            "Problems": "Website could not be fetched: " + str(r["fetch_error"]),
            "Missing Features": "", "Recommendations": "", "Pages Found": "",
            "Contact Info": "", "Contact Form": "", "Social Links": "",
            "CTA Count": "", "Mobile Indicators": "",
        })
        continue
    f_ = r["facts"]; j_ = r["ai_judgment"]
    csv_rows.append({
        "Website": r["final_url"],
        "Score": j_["score"],
        "Priority": j_["priority"],
        "Problems": " | ".join(j_["problems"]),
        "Missing Features": " | ".join(j_["missing_features"]),
        "Recommendations": " | ".join(j_["recommendations"]),
        "Pages Found": f_["discoverable_internal_links_count"],
        "Contact Info": ", ".join(f_["contact_info"]["emails_found"]) or "None",
        "Contact Form": f_["contact_form"]["likely_contact_form_detected"],
        "Social Links": ", ".join(f_["social_links_found"].keys()) or "None",
        "CTA Count": len(f_["cta_buttons_found"]),
        "Mobile Indicators": f_["mobile_indicators"]["viewport_meta_tag_present"],
    })
pd.DataFrame(csv_rows).to_csv("audit_report.csv", index=False)

with open("audit_report.md", "w") as f:
    f.write(markdown_report)

print("\nSaved: audit_report.md, audit_report.json, audit_report.csv")
print(f"FAISS index currently holds {faiss_index.ntotal} vectors from {len(metadata_store)} chunks.")

# ---------------------------------------------------------------------------
# PART Q — MANUAL REVIEW TEMPLATE (fill this in yourself — do not fabricate)
# ---------------------------------------------------------------------------
manual_review_template = """
MANUAL REVIEW TEMPLATE (review at least TWO AI outputs yourself)
------------------------------------------------------------------
Website: <paste URL>
AI Score: <copy from report>
My Score: <your own honest score after reading the page>
Difference: <AI score minus your score>
Would I change the AI result? <Yes/No>
Why?: <your reasoning, referencing something the AI got right or wrong>
------------------------------------------------------------------
Website: <paste second URL>
AI Score:
My Score:
Difference:
Would I change the AI result?
Why?:
"""
print(manual_review_template)
