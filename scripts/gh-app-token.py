#!/usr/bin/env python3.12
"""Generate a fresh GitHub App installation token and configure gh CLI to use it."""

import jwt, time, json, urllib.request, os, subprocess

APP_ID = 2862057
PEM_PATH = os.path.expanduser("~/.nanobot/github-app.pem")

with open(PEM_PATH, 'r') as f:
    private_key = f.read()

# Generate JWT
now = int(time.time())
payload = {'iat': now - 60, 'exp': now + (10 * 60), 'iss': APP_ID}
jwt_token = jwt.encode(payload, private_key, algorithm='RS256')

# Get installation ID
config_path = os.path.expanduser("~/.nanobot/github-app-config.json")
with open(config_path) as f:
    config = json.load(f)

install_id = config['installation_id']

# Get installation access token
req = urllib.request.Request(
    f'https://api.github.com/app/installations/{install_id}/access_tokens',
    method='POST',
    headers={'Authorization': f'Bearer {jwt_token}', 'Accept': 'application/vnd.github+json'}
)
resp = json.loads(urllib.request.urlopen(req).read())
token = resp['token']

# Output token (can be used by shell scripts)
print(token)
