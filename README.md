# AI Notes & Document Assistant

[![Django](https://img.shields.io/badge/Django-5.1-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![Tests](https://img.shields.io/badge/Tests-84%20Passed-success?style=for-the-badge)](#automated-testing--quality-assurance)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

A professional, full-stack, AI-augmented knowledge management and document analysis web application built with **Python 5 / Django 5.1**, **Bootstrap 5.3**, and **SQLite / PostgreSQL**. Engineered specifically as an internship-ready portfolio project for a B.Tech Artificial Intelligence & Machine Learning student.

The system combines structured note organization, dual authentication (Password & Email OTP), an **AI Document Studio** (summarization, style-based text polishing, bullet point extraction, and grounded Q&A over user-provided text), automated quiz generation with tamper-proof server-side scoring, and a privacy-grounded **"Ask My Notes"** retrieval engine.

---

## Table of Contents

1. [Project Overview & Problem Statement](#project-overview--problem-statement)
2. [Key Features & Capabilities](#key-features--capabilities)
3. [Technology Stack](#technology-stack)
4. [System Architecture](#system-architecture)
5. [Database Design & Entity Relationships](#database-design--entity-relationships)
6. [Dual Authentication & Recovery Workflows](#dual-authentication--recovery-workflows)
7. [AI Architecture & Capabilities](#ai-architecture--capabilities)
8. [Security & Privacy Engineering](#security--privacy-engineering)
9. [Local Installation & Setup Guide](#local-installation--setup-guide)
10. [Automated Testing & Quality Assurance](#automated-testing--quality-assurance)
11. [AI Provider Configuration Guide](#ai-provider-configuration-guide)
12. [Portfolio Screenshots Guide](#portfolio-screenshots-guide)
13. [Troubleshooting FAQ](#troubleshooting-faq)
14. [Internship Interview Defense Guide](#internship-interview-defense-guide)

---

## Project Overview & Problem Statement

### The Problem
Students and engineers frequently take unstructured notes across subjects like Machine Learning, Algorithms, System Design, and Cybersecurity. However, standard note apps suffer from four key issues:
1. **Passive Retention**: Reading static notes without active recall testing results in low retention.
2. **AI Hallucinations**: General LLMs answer questions from web-scale data rather than strictly referencing the student's verified course notes.
3. **Rough Drafting**: Raw lecture notes are often fragmented, poorly formatted, or filled with abbreviations.
4. **Privacy & API Costs**: Sending private study documents to expensive cloud APIs creates privacy concerns and recurring API expenses.

### The Solution: AI Notes & Document Assistant
- **Topic & Category Organization**: Hierarchical notebook structure with dated learning logs and keyword search.
- **AI Document Studio**: Paste any document or lecture excerpt to instantly **summarize**, **extract key points**, **improve writing style**, or **ask questions** answered strictly using the provided text.
- **Side-by-Side Text Improver**: Refine grammar and syntax with 4 distinct styles (*Professional*, *Concise Bullets*, *Technical*, *Academic*) and apply updates with one click.
- **Dual Authentication**: Seamless login via Username/Email + Password OR 6-digit One-Time Password (OTP) tied to the **same** Django user account.
- **Zero-Config Local Development**: Dispatches OTPs directly to the terminal banner during local development—**no external SMTP service required**.
- **Tamper-Proof AI Quizzes**: Generates 4-choice multiple-choice tests with server-side score calculation (`Choice.is_correct`), preventing client-side answer inspection.
- **Zero-Cost Local Heuristic Mode**: Operates out of the box with zero API costs, with plug-and-play support for Groq, Ollama, OpenAI, or Gemini.

---

## Key Features & Capabilities

### 1. Dual Authentication & Session Management
- **Unified Account System**: Password login and Email OTP login authenticate into the exact same Django `User` model.
- **HMAC-SHA256 Protected OTPs**: OTPs are hashed using HMAC-SHA256 with the server's `SECRET_KEY`; plain text codes are never saved in the database.
- **Terminal OTP Display (Dev Only)**: During local development, the 6-digit OTP is printed directly in a prominent console banner for effortless testing.
- **Security Hardening**: 5-minute expiry, single-use invalidation, 5-attempt brute-force lockout, and a 60-second cooldown against email bombing.
- **Password Recovery**: Cryptographically signed time-limited password reset links with modern security redirection.

### 2. Personal Notes & Category Management (CRUD)
- **Categories / Topics**: Create, view, edit, and delete study categories with timestamp tracking and live entry counts.
- **Note Entries**: Full Markdown-friendly entries with edit/delete confirmation safeguards.
- **Global Search**: Instant multi-attribute search across note titles, contents, and categories.

### 3. AI Document Studio (User-Provided Text Analysis)
- **Document Summarizer**: Generates executive summaries and key takeaways from arbitrary pasted text or saved notes.
- **Key Points Extractor**: Distills dense documents into bulleted insights for fast exam revision.
- **Style-Based Text Improver**: Polishes writing into *Professional*, *Concise Bullets*, *Technical*, or *Academic* tones.
- **Grounded Document Q&A**: Answers user questions strictly based on the provided document text, explicitly refusing to hallucinate if the answer is not present.
- **Direct Note Saving**: Save any AI-generated summary or improved document directly into your personal notebooks.

### 4. Interactive AI Quizzes & Tamper-Proof Testing
- **Dynamic Generation**: Generates 3 to 10 multiple-choice questions per note with 4 distinct options.
- **Server-Side Grading**: Evaluation occurs exclusively on the Django backend; answers and solution flags are never exposed in client form HTML.
- **Historical Score Tracking**: Tracks quiz attempts, percentage mastery, and question-level review explanations.

### 5. Grounded "Ask My Notes" Chatbot
- Conversational assistant querying exclusively across the authenticated user's private database notes.
- Multi-session chat history with session clearing and source note citations.

---

## Technology Stack

| Layer | Technologies |
|---|---|
| **Backend Framework** | Python 3.10+ &bull; Django 5.1 |
| **Database** | SQLite (Local Development) &bull; PostgreSQL (Production via `dj-database-url`) |
| **Frontend & UI** | Django Templates &bull; Bootstrap 5.3 &bull; Bootstrap Icons &bull; Vanilla JavaScript |
| **Authentication** | Django Session Auth &bull; PBKDF2 Password Hashing &bull; HMAC-SHA256 OTP Tokens |
| **AI Integration** | Decoupled Factory Architecture (`ai_service.py`): Mock Engine (Zero Cost), Groq, Ollama, OpenAI, Gemini |
| **Static Assets** | WhiteNoise 6.12 (Production asset compression & caching) |
| **Test Automation** | Django `TestCase` with `django.test.Client` (84 automated tests) |

---

## System Architecture

```
+-------------------------------------------------------------------------+
|                              Web Browser                                |
|   (Responsive Sidebar, Dashboard Cards, Document Studio, Forms, Modals) |
+-------------------------------------------------------------------------+
                                    |
                             HTTPS / HTTP
                                    v
+-------------------------------------------------------------------------+
|                             Django Core                                 |
|  - Security Middleware (CSRF, Clickjacking, Host Validation)             |
|  - Custom Auth Backend (EmailOrUsernameModelBackend)                     |
|  - Context Processors (ai_status_processor, auth, messages)             |
+-------------------------------------------------------------------------+
                                    |
                                    v
       +---------------------------------------------------------+
       |                 Django Views (views.py)                 |
       |  (Ownership checks: topic__user=request.user, user=req) |
       +---------------------------------------------------------+
              |                                          |
        ORM Queries                                AI Operations
              |                                          |
              v                                          v
+-----------------------------+         +-------------------------------+
|    Django Models & ORM      |         |     AI Service Abstraction     |
| (Topic, Entry, Summary,     |         |  (ai_service.get_ai_service)  |
|  Quiz, Question, Choice,    |         +-------------------------------+
|  QuizAttempt, ChatSession,  |                    |            |
|  EmailOTP)                  |         [Default]  |            | [Configured]
+-----------------------------+                    v            v
              |                             +------------+ +------------+
              v                             |  Mock NLP  | | Groq /     |
+-----------------------------+             |  Provider  | | Ollama /   |
| SQLite / PostgreSQL Database |             | (Zero Cost)| | OpenAI API |
+-----------------------------+             +------------+ +------------+
```

---

## Database Design & Entity Relationships

The relational schema implements full normalization and strict database integrity constraints:

```
+------------------------------------+
|        django.contrib.auth         |
|                User                |
+------------------------------------+
| id          : BigAutoField (PK)    |
| username    : CharField (Unique)   |
| email       : EmailField           |
| password    : CharField (PBKDF2)   |
+------------------------------------+
       |          |            |             |              |
     1:N        1:N          1:N           1:N            1:N
       v          v            v             v              v
+-------------+ +----------+ +-----------+ +------------+ +------------+
|    Topic    | | Summary  | |QuizAttempt| |ChatSession | |  EmailOTP  |
+-------------+ +----------+ +-----------+ +------------+ +------------+
| id (PK)     | | id (PK)  | | id (PK)   | | id (PK)    | | id (PK)    |
| user_id(FK) | | user_id  | | user_id   | | user_id    | | user_id(FK)|
| title       | | entry_id | | quiz_id   | | title      | | email      |
| description | | summary  | | score     | | created_at | | otp_hash   |
| created_at  | | key_pts  | | percentage| +------------+ | attempts   |
+-------------+ +----------+ +-----------+       |        | expires_at |
       |                                         1:N      | is_used    |
     1:N                                         v        +------------+
       v                                   +------------+
+-------------+                            |ChatMessage |
|    Entry    |                            +------------+
+-------------+                            | id (PK)    |
| id (PK)     |                            | session_id |
| topic_id(FK)|                            | role       |
| title       |                            | content    |
| content     |                            +------------+
| created_at  |
+-------------+
    |       |
  1:N     1:N
    |       |
    v       v
+-------------+
|    Quiz     |
+-------------+
| id (PK)     |
| entry_id(FK)|
| title       |
+-------------+
       |
     1:N
       v
+-------------+       1:N       +-------------+
|  Question   | --------------> |   Choice    |
+-------------+                 +-------------+
| id (PK)     |                 | id (PK)     |
| quiz_id(FK) |                 | question_id |
| text        |                 | text        |
| explanation |                 | is_correct  |
+-------------+                 +-------------+
```

---

## Dual Authentication & Recovery Workflows

### 1. Dual Login Flow (Password or OTP)
Users can authenticate using either method from the tabbed login page (`/login/`):
- **Password Authentication**: Enter Username or Email with password. Handled by `EmailOrUsernameModelBackend`.
- **Email OTP Authentication**:
  1. User enters their email address.
  2. Server enforces a 60-second cooldown rate limit against email bombing.
  3. If registered, a 6-digit OTP is generated and stored as an HMAC-SHA256 signature.
  4. **In Development**: The OTP is printed in a prominent terminal banner.
  5. **In Production**: The OTP is dispatched via SMTP.
  6. The user verifies the code at `/verify-otp/`. Successful verification logs into the user's account and marks the OTP as used (`is_used=True`).
  7. If the email is unregistered, the identical generic confirmation message is shown to prevent account enumeration.

### 2. Development Terminal OTP Output
When running locally (`DEBUG=True`), requesting an OTP prints this banner directly in your running terminal:

```text
================================================================================
[LOCAL DEVELOPMENT ONLY] AI NOTES & DOCUMENT ASSISTANT - OTP VERIFICATION
--------------------------------------------------------------------------------
Account Username : student_dev
Destination Email: student@example.com
One-Time Password: 749201
Validity Window  : 5 Minutes (Single-Use Only)
NOTE: This console output is for local development and demonstration only.
In production, this code is securely dispatched via SMTP to the user's email.
================================================================================
```

---

## AI Architecture & Capabilities

### Decoupled Factory Design
All AI interactions run through `learning_logs/ai_service.py` via `get_ai_service()`. The application switches providers without changing view or model logic:

```python
from learning_logs.ai_service import get_ai_service

service = get_ai_service()
summary = service.summarize(title, content)
improved = service.improve_text(content, style="professional")
doc_analysis = service.analyze_document(text, task="qa", question="What is gradient descent?")
```

### Prompt Injection Defense & Sanitization
All user-authored texts are treated as untrusted reference data:
1. **Length Capping**: Payloads truncated to 10,000 characters to prevent DoS or token context overflow.
2. **Null-Byte Stripping**: Null characters (`\x00`) are stripped before parsing.
3. **Delimiter Boundaries**: User inputs are strictly wrapped in demarcation blocks (`<notes>`, `<document>`) with system prompt directives forbidding command execution inside notes.
4. **Grounded Refusal**: If a question cannot be answered strictly from the user's text, the model returns an explicit refusal rather than hallucinating external facts.

---

## Security & Privacy Engineering

1. **Object-Level Authorization**:
   Every query filters strictly by user:
   ```python
   topic = get_object_or_404(Topic, id=topic_id, user=request.user)
   entry = get_object_or_404(Entry, id=entry_id, topic__user=request.user)
   ```
   Attempting to manipulate URL IDs yields an immediate `404 Not Found`.
2. **Tamper-Resistant Quiz Scoring**:
   The quiz form transmits only choice IDs. Correct answers are never sent in hidden input fields or JavaScript. Grading runs exclusively against server database records.
3. **Zero Secrets in Frontend or Git**:
   API keys and `SECRET_KEY` are read exclusively from environment variables via `python-dotenv` and ignored by `.gitignore`.
4. **CSRF & Password Hashing**:
   All POST endpoints require valid `{% csrf_token %}` tokens. Passwords use Django's PBKDF2 with SHA-256 algorithm.

---

## Local Installation & Setup Guide

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.14
- Git

### Step-by-Step Instructions

#### 1. Navigate to Project Directory
```bash
cd /home/sukh/personal_knowledge_system
```

#### 2. Create and Activate Virtual Environment
```bash
# Linux / macOS
python3 -m venv venv
source venv/bin/activate

# Windows (Command Prompt)
python -m venv venv
venv\Scripts\activate.bat

# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default `.env` configuration (ready for immediate local use):
```ini
SECRET_KEY=django-insecure-learning-logs-dev-key-change-in-production-12345
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,[::1]
AI_PROVIDER=mock
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

#### 5. Apply Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

#### 6. (Optional) Populate Sample Portfolio Data
To seed initial categories and notes across Machine Learning, Cybersecurity, and Web Development:
```bash
python manage.py seed_demo_data
```
Created demo credentials:
- **Username**: `demo_student`
- **Email**: `demo_student@example.com`
- **Password**: `DemoStudent123!`

#### 7. Launch the Development Server
```bash
python manage.py runserver
```
Open your browser at **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**.

---

## Automated Testing & Quality Assurance

The project includes an automated test suite containing **84 test cases** verifying authentication, authorization, CRUD logic, AI mock generation, scoring security, retrieval isolation, OTP lifecycle, and password recovery:

```bash
python manage.py test
```

### Test Coverage Highlights (84 Tests Across 13 Test Classes)
- `ModelTests`: String representations, snippet previews, entry counts.
- `AuthenticationTests`: Registration validation, duplicate checks, login/logout.
- `DualLoginAndOTPAuthenticationTests`:
  - Password login with username or email.
  - OTP challenge creation and terminal output.
  - Enumeration defense for unregistered emails.
  - Single-use invalidation, 5-minute expiry, and 5-attempt lockout.
  - 60-second cooldown rate limit enforcement.
- `DocumentAssistantAndTextImproverTests`:
  - Document summarization and key points extraction on arbitrary text.
  - Style-based text improvement (*Professional*, *Concise*, *Technical*, *Academic*).
  - Grounded document Q&A matching and refusal behavior.
  - Direct saving of AI results to user notebooks.
  - Multi-tenant access rejection (cannot save to or improve another user's note).
- `AccessControlAndOwnershipTests`: Verification that User Bob cannot view, edit, or delete User Alice's notes or categories.
- `QuizAndScoringTests`: Server-side scoring verification and client-side score manipulation defense.
- `AskNotesChatbotTests`: Multi-tenant retrieval isolation in private Q&A.

---

## AI Provider Configuration Guide

The application runs in **Mock AI Mode** by default. To connect a live model, update `.env`:

### Option A: Free High-Speed Cloud Inference with Groq (Recommended)
1. Get a free API key at [console.groq.com](https://console.groq.com).
2. Set in `.env`:
   ```ini
   AI_PROVIDER=groq
   AI_API_KEY=gsk_your_actual_groq_api_key
   AI_MODEL=llama-3.3-70b-versatile
   ```

### Option B: 100% Private Local Offline LLM with Ollama
1. Install [Ollama](https://ollama.ai) and pull a model:
   ```bash
   ollama run llama3.2
   ```
2. Set in `.env`:
   ```ini
   AI_PROVIDER=ollama
   AI_BASE_URL=http://localhost:11434/v1
   AI_MODEL=llama3.2
   ```

### Option C: OpenAI
```ini
AI_PROVIDER=openai
AI_API_KEY=sk-your_actual_openai_key
AI_MODEL=gpt-4o-mini
```

### Option D: Google Gemini
```ini
AI_PROVIDER=gemini
AI_API_KEY=your_gemini_api_key
AI_MODEL=gemini-1.5-flash
AI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
```

---

## Portfolio Screenshots Guide

To showcase this project effectively on GitHub, LinkedIn, or in an internship portfolio, capture screenshots of the following workflows:

1. **Dashboard & Sidebar Layout** (`/dashboard/`):
   - Shows sidebar navigation, quick action buttons, statistics cards, and recent notes.
2. **AI Document Studio** (`/document-assistant/`):
   - Shows pasted study text on the left and generated executive summary, key points, and direct notebook saving on the right.
3. **Side-by-Side AI Text Improver** (`/entries/<id>/improve/`):
   - Shows original text vs. AI improved text with style selection (*Professional*, *Technical*, etc.).
4. **Interactive AI Quiz Interface & Server-Side Results** (`/quizzes/<id>/`):
   - Shows 4-choice questions and the post-submission grading breakdown with percentage scores and rationale.
5. **Terminal OTP Banner Demonstration**:
   - Screenshot of the terminal running `runserver` displaying the `[LOCAL DEVELOPMENT ONLY]` OTP verification banner alongside the web browser login page.

---

## Troubleshooting FAQ

### 1. `Port 8000 is already in use`
Run the development server on a different port:
```bash
python manage.py runserver 8080
```

### 2. Where do I find the OTP code during local testing?
Check the terminal where `python manage.py runserver` is running. The OTP is printed inside an unmistakable `[LOCAL DEVELOPMENT ONLY]` box.

### 3. I configured an external AI key, but it's showing Mock Mode
Check that `AI_API_KEY` is not empty in your `.env` file and that `AI_PROVIDER` matches your provider name (`groq`, `openai`, `gemini`, or `ollama`). If the API endpoint is unreachable or credentials fail, the application gracefully falls back to Mock Mode without crashing.

---

## Internship Interview Defense Guide

When presenting this project during technical internship interviews, highlight these engineering decisions:

1. **Why Django instead of a microframework like Flask/FastAPI?**
   > *"Django provides robust, battle-tested built-ins for ORM, session authentication, CSRF protection, and migration management. This allowed me to focus on business logic, object-level security, and decoupled AI services without reinventing secure authentication."*

2. **How does the OTP system prevent user enumeration?**
   > *"When a user requests an OTP or password reset, the server returns the exact same generic confirmation message ('If an account exists, a code was sent') regardless of whether the email is present in the database. This prevents attackers from brute-forcing valid email addresses."*

3. **How is the AI integration safeguarded against prompt injection?**
   > *"User notes are treated as untrusted reference data. They are length-capped, sanitized of null bytes, and enclosed in explicit boundary tags (`<notes>`, `<document>`) with strict system prompt directives instructing the model never to execute instructions embedded within the text."*

4. **How is quiz cheating prevented?**
   > *"Scoring is strictly server-side. The client HTML never receives `is_correct` flags or solution keys. Grading validates submitted choice IDs against the database record."*
