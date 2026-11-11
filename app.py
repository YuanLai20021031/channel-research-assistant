"""Local, single-user channel research prototype. No mail is sent."""
import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit

from flask import Flask, jsonify, render_template, request

ROOT = Path(__file__).parent


class ResearchError(Exception):
    pass


def search_channels(brief):
    key = os.getenv('TAVILY_API_KEY')
    if key is None:
        env_file = ROOT / '.env'
        if env_file.is_file():
            for line in env_file.read_text(encoding='utf-8').splitlines():
                if line.startswith('TAVILY_API_KEY='):
                    key = line.partition('=')[2].strip().strip('\"').strip("'")
                    break
    if not key:
        raise ResearchError('Live search is not configured. Set TAVILY_API_KEY on the server, or choose the clearly labelled sample mode.')
    query = f"{brief['market']} {brief['audience']} {brief['product']} newsletter community publication contribute partnership"
    req = Request('https://api.tavily.com/search', data=json.dumps({
        'query': query, 'max_results': 8, 'search_depth': 'basic',
        'include_answer': False,
    }).encode(), headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'})
    try:
        with urlopen(req, timeout=25) as response:
            data = json.load(response)
    except HTTPError as exc:
        raise ResearchError(f'Search provider returned HTTP {exc.code}. Check the API key or quota and retry.') from exc
    except (URLError, TimeoutError, ValueError) as exc:
        raise ResearchError('Search is unavailable. Check your connection and retry; existing saved reports are unaffected.') from exc
    results, seen = [], set()
    for item in data.get('results', []):
        url = item.get('url', '')
        parsed = urlsplit(url)
        host = parsed.hostname or ''
        content = item.get('content', '')
        if parsed.scheme != 'https' or not host or host in seen or not content:
            continue
        # Conservative first version: only retain snippets with a channel signal.
        if not any(term in content.lower() for term in ('newsletter', 'community', 'contributor', 'editorial', 'publication', 'partnership')):
            continue
        seen.add(host)
        results.append({
            'name': item.get('title') or host, 'url': url,
            'evidence': content[:900], 'source': url,
            'reason': f"Discovery candidate for {brief['audience']} in {brief['market']}. The search excerpt mentions a publishing, community or partnership activity; product suitability still needs manual review.",
            'unknown': 'Audience geography, submission rules, current contact and acceptance of product-related content have not been independently verified.',
        })
        if len(results) == 3:
            break
    return results


def sample_channels(brief):
    market = brief['market'].lower()
    audience = brief['audience'].lower()
    product = brief['product'].lower()
    uk = any(x in market for x in ('uk', 'united kingdom', 'britain'))
    small = any(x in audience for x in ('small business', 'small team', 'sme'))
    tasks = any(x in product for x in ('task', 'project management'))
    if not (uk and small and tasks):
        return []
    return [
        {'name': 'Small Business UK', 'url': 'https://smallbusiness.co.uk/',
         'source': 'https://smallbusiness.co.uk/contact-us/',
         'evidence': 'The contact page describes support for owner-managers of businesses with up to 50 employees and considers suitable one-off contributor articles. Source reviewed on 9 November 2026.',
         'reason': 'Its owner-manager audience overlaps with UK small-business buyers. A practical article about assigning tasks and tracking deadlines is a plausible editorial pitch; this is our inference, not a publisher endorsement.',
         'unknown': 'Acceptance, editorial requirements and any commercial terms must be confirmed. The audience is broader than teams of 1–20.'},
        {'name': 'Small Business Britain', 'url': 'https://smallbusinessbritain.uk/',
         'source': 'https://smallbusinessbritain.uk/contact',
         'evidence': 'The contact page invites organisations interested in working with the team and offers a newsletter about small-business campaigns, programmes and events. Source reviewed on 9 November 2026.',
         'reason': 'The UK small-business focus makes an educational session on team coordination worth exploring. A product demonstration is a proposed idea, not a confirmed opportunity.',
         'unknown': 'Commercial product eligibility, newsletter placement and audience team sizes are unconfirmed.'},
        {'name': 'SmallBusinessPro', 'url': 'https://www.smallbusinesspro.co.uk/',
         'source': 'https://www.smallbusinesspro.co.uk/contact.html',
         'evidence': 'The contact page invites prospective authors and original articles through its contact form. Source reviewed on 9 November 2026.',
         'reason': 'A small-business publication with a stated article submission route may suit a useful guide to managing deadlines and responsibilities.',
         'unknown': 'Current editorial activity, promotional-content policy, readership and acceptance are unconfirmed.'},
    ]


def draft_email(brief, channel):
    return (f"Subject: Practical content collaboration enquiry\n\nHello {channel['name']} team,\n\n"
            f"I am getting in touch about a product described as follows: {brief['product']}\n\n"
            f"It is intended for {brief['audience']} in {brief['market']}. We are exploring relevant channels and would like to ask whether a practical educational article or a short product demonstration could be suitable for your audience.\n\n"
            "Would you be open to reviewing a brief outline? Please let us know your submission guidelines, the appropriate contact, and any applicable commercial terms. We would be happy to adapt the proposal to your editorial requirements.\n\n"
            "Kind regards,\n[Your name]\n[Product / company]\n[Contact details]")


def create_app(database=None):
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 16000
    path = Path(database or ROOT / 'instance' / 'research.db')
    path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect():
        conn = sqlite3.connect(path)
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    with connect() as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS reports (id TEXT PRIMARY KEY, created TEXT NOT NULL, body TEXT NOT NULL)')

    @app.get('/')
    def index():
        return render_template('index.html')

    @app.get('/api/reports')
    def history():
        with connect() as conn:
            rows = conn.execute('SELECT body FROM reports ORDER BY created DESC LIMIT 50').fetchall()
        return jsonify([json.loads(row[0]) for row in rows])

    @app.post('/api/research')
    def research():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(error='Please submit a valid JSON brief.'), 400
        brief = {}
        for field in ('product', 'audience', 'market'):
            value = data.get(field)
            if not isinstance(value, str) or not 2 <= len(value.strip()) <= 1500:
                label = {'product': 'Product description', 'audience': 'Target customers', 'market': 'Target market'}[field]
                return jsonify(error=f'{label}: enter between 2 and 1500 characters.'), 400
            brief[field] = value.strip()
        mode = data.get('mode', 'sample')
        if mode not in ('sample', 'live'):
            return jsonify(error='Unknown research mode.'), 400
        try:
            channels = sample_channels(brief) if mode == 'sample' else search_channels(brief)
        except ResearchError as exc:
            return jsonify(error=str(exc)), 502
        report = {'id': str(uuid.uuid4()), 'created': datetime.now(timezone.utc).isoformat(),
                  'brief': brief, 'mode': mode, 'channels': channels,
                  'notice': ('Sample evidence library, reviewed 9 November 2026. Supports UK small-business task-management briefs only. No live search was performed.' if mode == 'sample' else 'Search excerpts only. Candidates are not fully verified recommendations. Open each source and confirm fit before contacting anyone.'),
                  'draft': draft_email(brief, channels[0]) if channels else '',
                  'next_step': '' if channels else 'No supported channels found. Refine the brief or configure live search. Do not infer that no suitable channels exist.'}
        try:
            with connect() as conn:
                conn.execute('INSERT INTO reports VALUES (?, ?, ?)', (report['id'], report['created'], json.dumps(report, ensure_ascii=False)))
        except sqlite3.Error:
            return jsonify(error='The report could not be saved. Check disk space and database permissions, then retry.'), 500
        return jsonify(report), 201

    @app.errorhandler(413)
    def too_large(error):
        return jsonify(error='The brief is too large. Shorten the input and retry.'), 413

    return app


if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=5055, debug=False)
