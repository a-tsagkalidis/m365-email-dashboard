# Required Libraries
import os
from app import app
from config import app_config
import flask
import requests
import msal
from flask import Flask, render_template, redirect, url_for, session

# Flask App Configuration
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Microsoft 365 App Registration Details
CLIENT_ID = app_config.CLIENT_ID
CLIENT_SECRET = app_config.CLIENT_SECRET
TENANT_ID = app_config.TENANT_ID
AUTHORITY = f'https://login.microsoftonline.com/{TENANT_ID}'
REDIRECT_PATH = '/getAToken'
SCOPE = ['Mail.Read', 'Mail.Send']

# MSAL Configuration
def _build_msal_app(cache=None):
    return msal.ConfidentialClientApplication(
        CLIENT_ID, authority=AUTHORITY,
        client_credential=CLIENT_SECRET, token_cache=cache)

def _build_auth_url():
    return _build_msal_app().get_authorization_request_url(SCOPE, redirect_uri=url_for('authorized', _external=True))

def _get_token_from_cache():
    cache = msal.SerializableTokenCache()
    if session.get('token_cache'):
        cache.deserialize(session['token_cache'])
    cca = _build_msal_app(cache)
    accounts = cca.get_accounts()
    if accounts:
        result = cca.acquire_token_silent(SCOPE, account=accounts[0])
        session['token_cache'] = cache.serialize()
        return result

# Routes
@app.route('/')
def index():
    token = _get_token_from_cache()
    if not token:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login')
def login():
    auth_url = _build_auth_url()
    return redirect(auth_url)

@app.route(REDIRECT_PATH)
def authorized():
    cache = msal.SerializableTokenCache()
    if session.get('token_cache'):
        cache.deserialize(session['token_cache'])
    result = _build_msal_app(cache).acquire_token_by_authorization_code(
        request.args['code'],
        scopes=SCOPE,
        redirect_uri=url_for('authorized', _external=True))
    if 'error' in result:
        return "Login failure: {}".format(result['error'])
    session['token_cache'] = cache.serialize()
    session['user'] = result.get('id_token_claims')
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    token = _get_token_from_cache()
    if not token:
        return redirect(url_for('login'))
    
    graph_data = requests.get(
        'https://graph.microsoft.com/v1.0/me/messages',
        headers={'Authorization': 'Bearer ' + token['access_token']},
        params={'$top': '10', '$select': 'subject,from,receivedDateTime'}
    ).json()

    return render_template('dashboard.html', emails=graph_data['value'])

# HTML Template for Dashboard
dashboard_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Email Dashboard</title>
</head>
<body>
    <h1>Recent Emails</h1>
    <table border="1">
        <tr>
            <th>Subject</th>
            <th>From</th>
            <th>Received Date</th>
        </tr>
        {% for email in emails %}
        <tr>
            <td>{{ email.subject }}</td>
            <td>{{ email.from.emailAddress.name }}</td>
            <td>{{ email.receivedDateTime }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

# Save the HTML template to a file
with open('templates/dashboard.html', 'w') as f:
    f.write(dashboard_html)

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)

