"""Minimal FFLogs v2 client for the maintainer-side importers.

Credentials come from a local `.env` (FFLOGS_CLIENTID / FFLOGS_CLIENTSECRET),
which is gitignored - nothing here is ever committed, and the access token is
held in memory for the life of the process, never written to disk.

Like scripts/fetch_icons.py this runs maintainer-side only. The site makes no
third-party network requests at runtime; see AGENTS.md.
"""
import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / '.env'
TOKEN_URL = 'https://www.fflogs.com/oauth/token'
CLIENT_URL = 'https://www.fflogs.com/api/v2/client'

_token = None


def load_env():
    """Read `.env` into os.environ without clobbering a real environment value."""
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def token():
    """Client-credentials access token, fetched once per process."""
    global _token
    if _token:
        return _token
    load_env()
    client_id = os.environ.get('FFLOGS_CLIENTID')
    secret = os.environ.get('FFLOGS_CLIENTSECRET')
    if not client_id or not secret:
        raise SystemExit('Set FFLOGS_CLIENTID and FFLOGS_CLIENTSECRET in .env')
    basic = base64.b64encode(f'{client_id}:{secret}'.encode()).decode()
    request = urllib.request.Request(
        TOKEN_URL,
        data=urllib.parse.urlencode({'grant_type': 'client_credentials'}).encode(),
        headers={'Authorization': f'Basic {basic}'},
    )
    with urllib.request.urlopen(request) as response:
        _token = json.load(response)['access_token']
    return _token


def query(document, **variables):
    """Run a GraphQL query and return its `data`, raising on any GraphQL error."""
    payload = json.dumps({'query': document, 'variables': variables}).encode()
    request = urllib.request.Request(
        CLIENT_URL,
        data=payload,
        headers={'Authorization': f'Bearer {token()}', 'Content-Type': 'application/json'},
    )
    try:
        with urllib.request.urlopen(request) as response:
            body = json.load(response)
    except urllib.error.HTTPError as error:
        raise SystemExit(f'FFLogs HTTP {error.code}: {error.read().decode()[:400]}')
    if body.get('errors'):
        raise SystemExit('FFLogs error: ' + json.dumps(body['errors'])[:600])
    return body['data']


def report_code(url_or_code):
    """Accept a report code or any fflogs.com/reports/<code> URL.

    The fight number rides in the query string on a copied link
    (`?fight=33&type=damage-done`) but in the fragment on an in-app one
    (`#fight=33`), so read both.
    """
    if '/' not in url_or_code:
        return url_or_code, None
    parsed = urllib.parse.urlparse(url_or_code)
    code = parsed.path.rstrip('/').split('/')[-1]
    fields = urllib.parse.parse_qs(parsed.query)
    fields.update(urllib.parse.parse_qs(parsed.fragment))
    value = (fields.get('fight') or [None])[0]
    return code, int(value) if value and value.isdigit() else None
