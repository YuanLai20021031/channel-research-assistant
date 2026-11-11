# Channel Research Assistant

**Author:** Lai Yuan  
**Project date:** 11 November 2026

A locally hosted Flask prototype for researching potential marketing and partnership channels. Enter a product description, target customers, and market; review a shortlist of candidates with supporting public sources and uncertainties; draft an outreach email; and reopen previously saved research reports.

> **Prototype status:** Live search has limited matching quality. Candidate channels are leads to investigate, **not** verified recommendations. The application does not send emails.

## Requirements

- Python 3.12 or newer
- Internet access to install dependencies
- Optional: a Tavily API key and internet access for live research

## Install and run

From the project directory, run the following commands in **Windows PowerShell**:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Open **http://127.0.0.1:5055** in your browser. Keep the terminal running and press `Ctrl+C` to stop the server. If the port is occupied, stop the previous instance. On macOS or Linux, create a virtual environment with `python3 -m venv .venv`, install dependencies with `.venv/bin/python -m pip install -r requirements.txt`, then run `.venv/bin/python app.py`.

## Use the application

1. Start with the pre-filled UK small-business task-management brief, select **Sample evidence library**, and click **Research channels**. This mode uses curated public sources, **not** a new live search.
2. Examine each candidate's source, rationale, and unverified details before making contact.
3. Select a channel and edit the English outreach draft. You can copy the draft or export the report as JSON. The tool does **not** send mail.
4. Reopen a report under **Saved research**. Reports are stored in the locally created `instance/research.db` database and persist after the browser closes.
5. For live searches, configure Tavily as described below and select **Live search**.

### Configure Tavily live search

Copy `.env.example` to `.env` in the project directory and add your own key:

```dotenv
TAVILY_API_KEY=your_actual_api_key
```

Alternatively, set the `TAVILY_API_KEY` environment variable; it takes precedence over `.env`. Never commit `.env` or post a real API key to GitHub. Live mode sends the product, customer, and market descriptions to Tavily. Do not enter confidential information. The service may incur charges or be limited by your API allowance. No language-model API key is required; email drafts are template-generated.

Tavily API reference: https://docs.tavily.com/documentation/api-reference/endpoint/search

## Example briefs

**Built-in sample mode** supports the following input:

| Field | Example |
|---|---|
| Product description | A task management product for teams of 1–20 people, with task assignment, deadline reminders and project progress tracking. |
| Target customers | Small business owners and small teams |
| Target market | United Kingdom |

Additional briefs to try in **live search** (they are *not* covered by the built-in sample library):

- **Small agencies** — Product: A project management tool that helps small marketing agencies assign client work, track campaign deadlines and monitor project progress. Customers: Owners and project managers at small digital marketing agencies. Market: United Kingdom.
- **Small e-commerce businesses** — Product: A team coordination tool for small online shops to assign daily tasks, track product launch deadlines and manage marketing activities. Customers: Small e-commerce business owners and operations managers. Market: United Kingdom.

If you are on a limited or free Tavily plan, searches may be restricted by your current provider quota.

## Tests

Run the unit tests using the Python environment where Flask is installed:

```powershell
.\.venv\Scripts\python.exe -m unittest -v
```

The five tests cover input validation, persisted reports, sample-scenario boundaries, missing API credentials, and mocked live-search deduplication. See [VALIDATION.md](VALIDATION.md) for the original test record and its limitations.

The provided `examples/sample_report.json` and `examples/outreach_email.txt` are sample-mode outputs. They are not evidence of a fresh live-search request.

## Project structure

| Path | Purpose |
|---|---|
| `app.py` | Flask endpoints, validation, research, email templates, SQLite storage |
| `templates/index.html` | English web interface |
| `static/app.js` | Browser interactions |
| `static/style.css` | Styling |
| `test_app.py` | Unit tests |
| `examples/` | Example report and email |
| `CONTRIBUTIONS.md` | AI assistance and author contribution disclosure |
| `VALIDATION.md` | Test and live API validation record |
| `.env.example` | Configuration template without secrets |

**API endpoints:** `POST /api/research` creates and saves a report; `GET /api/reports` retrieves up to 50 recent reports.

## Known limitations

1. Live search submits one Tavily query, receives at most eight results, and selects up to three candidates using signal keywords and hostname deduplication. The results may be irrelevant (e.g., product-review sites) or empty. An empty result does not imply that no channels exist.
2. Audience, geography, submission rules, and partnership contact details are **not** thoroughly verified automatically.
3. Sample mode only covers the supplied UK small-business task-management scenario; it is not general-purpose discovery.
4. Email drafts are generated from a fixed English template. Selecting another channel mainly changes the salutation. Non-English brief text is **not** automatically translated, and commercial claims must be checked before sending.
5. Report data is saved automatically, but changes made to a draft in the browser are not persisted. Copy or export the edited draft before leaving. Only the latest 50 reports appear in history.
6. Changing the input fields does not invalidate a previously displayed report until you run research again. Check the report's brief and timestamp.
7. This is a local, single-user development prototype without account management, job queues, or production security controls. **Do not expose the running Flask server directly to the public internet.**
8. Public source content can change. Open original links and verify all details before outreach.

## Sources and credits

The application uses Flask (BSD-3-Clause) and the Python standard library. Sample channel references:

- https://smallbusiness.co.uk/contact-us/
- https://smallbusinessbritain.uk/contact
- https://www.smallbusinesspro.co.uk/contact.html

See [CONTRIBUTIONS.md](CONTRIBUTIONS.md) for a transparent account of AI assistance and the author's work.
