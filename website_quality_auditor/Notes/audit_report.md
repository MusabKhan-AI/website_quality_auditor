# AI-Assisted Website Quality Audit Report

## Executive Summary
* **Total Websites Analyzed:** 5
* **Report Date:** 2026-09-11
* **Primary Framework:** RAG via FAISS Vector DB + Groq LLM Grounding
* **Methodology:** Automated deterministic HTML parsing (Facts) combined with AI-based quality judgment.

---

## 📊 Summary Audit Table

| Website URL | Facts Detected (Contact / Form / Social / CTAs / Pages) | AI Score | Priority | Key Issues / Missing Features | Recommendations |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **`https://www.stripe.com`** | **Email:** None<br>**Form:** No<br>**Social:** YouTube<br>**CTAs:** 8 found<br>**Pages Found:** 60 | **86/100** | **Low** | • No direct email contact visible on landing page<br>• Contact forms embedded behind sub-pages | • Add direct email/lead form in footer<br>• Streamline enterprise contact process |
| **`https://www.shopify.com`** | **Email:** None<br>**Form:** No<br>**Social:** FB, TW, YT, IG, TikTok, LinkedIn<br>**CTAs:** 2 found<br>**Pages Found:** 60 | **84/100** | **Low** | • No phone number or immediate contact details<br>• Focus is heavily driven towards trial signup | • Include dedicated sales contact link above fold<br>• Show direct support access points |
| **`https://www.hubspot.com`** | **Email:** None<br>**Form:** No (2 forms detected)<br>**Social:** FB, IG, YT, X, LinkedIn, TikTok<br>**CTAs:** 20+ found<br>**Pages Found:** 60 | **90/100** | **Low** | • High volume of CTAs may cause decision fatigue<br>• Complex navigation structure | • Simplify primary hero section CTAs<br>• Group sub-products more clearly |
| **`https://www.slack.com`** | **Email:** None<br>**Form:** No<br>**Social:** YT, LinkedIn, IG, FB, Twitter, TikTok<br>**CTAs:** 13 found<br>**Pages Found:** 1 | **82/100** | **Medium** | • Internal page discoverability capped on main entry<br>• Contact form absent from main page | • Add quick-contact form for enterprise leads<br>• Improve internal cross-linking visibility |
| **`https://www.zoho.com`** | **Email:** None<br>**Form:** No<br>**Social:** None detected<br>**CTAs:** 3 found<br>**Pages Found:** 13 | **75/100** | **Medium** | • Missing social media links on primary homepage<br>• Lower visible text length and navigation depth | • Embed social proof and social media links<br>• Expand homepage feature summary |

---

## Detailed Website Breakdown

### Website 1: Stripe (https://www.stripe.com)

#### [FACT — AUTOMATICALLY DETECTED]
* **Discoverable internal links/pages found:** 60 (capped)
* **Emails found:** None detected
* **Phone-like pattern detected:** True
* **Contact/About link found:** True
* **Address-related terms found:** False
* **Contact form detected:** No (0 `<form>` tag(s) found)
* **Social links found:** `['youtube.com']`
* **CTA buttons found:** `['Contact sales', 'Get started', 'Sign up with Google', 'Start now', 'Startups', ...]`
* **Navigation links found:** 7
* **Mobile/responsive basic indicators:** Viewport Tag = True, Responsive CSS Hint = True
* **Page word count:** 1,884 words

#### [AI JUDGMENT — GENERATED FROM AVAILABLE EVIDENCE]
* **Score:** 86 / 100
* **Priority:** Low
* **Problems Identified:**
  1. No direct email address published on the primary homepage text.
  2. Lead capture forms require navigating away from the landing page.
* **Missing Features:**
  1. Embedded quick-inquiry contact form on the main homepage.
* **Recommendations:**
  1. Add a streamlined inquiry form in the footer or contact section.
  2. Highlight secondary support channels clearly.

---

### Website 2: Shopify (https://www.shopify.com)

#### [FACT — AUTOMATICALLY DETECTED]
* **Discoverable internal links/pages found:** 60 (capped)
* **Emails found:** None detected
* **Phone-like pattern detected:** False
* **Contact/About link found:** False
* **Address-related terms found:** False
* **Contact form detected:** No (0 `<form>` tag(s) found)
* **Social links found:** `['facebook.com', 'twitter.com', 'youtube.com', 'instagram.com', 'tiktok.com', 'linkedin.com']`
* **CTA buttons found:** `['Get started fastYou could be selling by tomorrow.', 'Start for free']`
* **Navigation links found:** 45
* **Mobile/responsive basic indicators:** Viewport Tag = True, Responsive CSS Hint = True
* **Page word count:** 1,258 words

#### [AI JUDGMENT — GENERATED FROM AVAILABLE EVIDENCE]
* **Score:** 84 / 100
* **Priority:** Low
* **Problems Identified:**
  1. High reliance on trial signups with limited direct human sales inquiry options on the homepage.
* **Missing Features:**
  1. Direct contact phone or immediate chat popup.
* **Recommendations:**
  1. Introduce a enterprise-level "Talk to Sales" CTA alongside the free trial button.

---

### Website 3: HubSpot (https://www.hubspot.com)

#### [FACT — AUTOMATICALLY DETECTED]
* **Discoverable internal links/pages found:** 60 (capped)
* **Emails found:** None detected
* **Phone-like pattern detected:** False
* **Contact/About link found:** True
* **Address-related terms found:** True
* **Contact form detected:** No (2 `<form>` tags found)
* **Social links found:** `['facebook.com', 'instagram.com', 'youtube.com', 'x.com', 'linkedin.com', 'tiktok.com']`
* **CTA buttons found:** 20+ distinct CTAs (`'Contact Sales'`, `'Get started free'`, `'Get a demo'`, etc.)
* **Navigation links found:** 191
* **Mobile/responsive basic indicators:** Viewport Tag = True, Responsive CSS Hint = True
* **Page word count:** 2,120 words

#### [AI JUDGMENT — GENERATED FROM AVAILABLE EVIDENCE]
* **Score:** 90 / 100
* **Priority:** Low
* **Problems Identified:**
  1. Navigation menu and CTA volume is extremely high, which can overwhelm new visitors.
* **Missing Features:**
  1. Simplified single-path landing experience for quick onboarding.
* **Recommendations:**
  1. Focus main hero section on two primary CTAs (e.g., "Get Demo" and "Try Free").

---

### Website 4: Slack (https://www.slack.com)

#### [FACT — AUTOMATICALLY DETECTED]
* **Discoverable internal links/pages found:** 1
* **Emails found:** None detected
* **Phone-like pattern detected:** False
* **Contact/About link found:** True
* **Address-related terms found:** False
* **Contact form detected:** No (0 `<form>` tag(s) found)
* **Social links found:** `['youtube.com', 'linkedin.com', 'instagram.com', 'facebook.com', 'twitter.com', 'tiktok.com']`
* **CTA buttons found:** 13 found (`'Contact Us'`, `'Get Started'`, `'Request a demo'`, etc.)
* **Navigation links found:** 374
* **Mobile/responsive basic indicators:** Viewport Tag = True, Responsive CSS Hint = False
* **Page word count:** 2,138 words

#### [AI JUDGMENT — GENERATED FROM AVAILABLE EVIDENCE]
* **Score:** 82 / 100
* **Priority:** Medium
* **Problems Identified:**
  1. Low discoverable homepage internal links on initial HTML crawl pass.
  2. Responsive CSS media tag heuristic returned False (relies on external stylesheet bundles).
* **Missing Features:**
  1. Inline contact form.
* **Recommendations:**
  1. Ensure inline CSS hints are detectable and optimize mobile viewport fallback tags.

---

### Website 5: Zoho (https://www.zoho.com)

#### [FACT — AUTOMATICALLY DETECTED]
* **Discoverable internal links/pages found:** 13
* **Emails found:** None detected
* **Phone-like pattern detected:** False
* **Contact/About link found:** True
* **Address-related terms found:** True
* **Contact form detected:** No (0 `<form>` tag(s) found)
* **Social links found:** None detected
* **CTA buttons found:** 3 found (`'Get Started For Free'`, `'Learn more'`, `'Sign Up Now'`)
* **Navigation links found:** 0
* **Mobile/responsive basic indicators:** Viewport Tag = True, Responsive CSS Hint = False
* **Page word count:** 568 words

#### [AI JUDGMENT — GENERATED FROM AVAILABLE EVIDENCE]
* **Score:** 75 / 100
* **Priority:** Medium
* **Problems Identified:**
  1. Social media profile links were not detected in the primary HTML header/footer.
  2. Page word count is lower compared to industry competitors.
* **Missing Features:**
  1. Visible social links and inline contact/lead form.
* **Recommendations:**
  1. Add official social channel icons in the footer and expand feature overview copy.

---

## Manual Review (Requirement #8)

### Review 1:
* **Website:** `https://www.stripe.com`
* **AI Score:** 86
* **My Score:** 82
* **Difference:** -4
* **Would I change the AI result?:** Yes
* **Why?:** While Stripe has exceptional design and CTA structure, the total absence of an inline contact form or visible email address on the main homepage makes it harder for high-intent enterprise users to make immediate contact. A slight deduction is warranted.

### Review 2:
* **Website:** `https://www.zoho.com`
* **AI Score:** 75
* **My Score:** 78
* **Difference:** +3
* **Would I change the AI result?:** Yes
* **Why?:** The AI scored Zoho lower due to missing social media links in the HTML crawl. However, Zoho's brand authority and clean call-to-action layout ("Get Started For Free") provide a solid user experience. I adjusted the score slightly higher to reflect actual brand usability.

---

## Prompt Improvement Analysis (V1 vs V2)
* **Prompt V1:** Sent raw extracted text to the LLM and asked for an open-ended quality score. This resulted in floating scores without standard criteria.
* **Prompt V2 (Used):** Introduced fixed category weights (Contact Info: 20%, CTAs: 15%, Trust Signals: 15%, Socials: 10%, etc.) and enforced strict JSON output with no hallucinated facts.

---

## Limitations
1. **Single Page Scope:** Only the homepage HTML is fetched and analyzed; sub-pages are not deeply crawled.
2. **Basic Mobile Checks:** Heuristics look for `<meta name="viewport">` and media query tags, which is not a substitute for real device rendering.
3. **Regex Constraints:** Contact phone and email detection relies on regex, which may miss non-standard obfuscated contact text.