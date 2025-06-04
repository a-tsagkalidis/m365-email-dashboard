import msal
import requests
from flask import (
    Blueprint,
    session,
    redirect,
    url_for,
    render_template,
    flash,
    request,
    current_app
)


maildash_bp = Blueprint('maildash', __name__)


def _build_msal_app(cache=None):
    return msal.ConfidentialClientApplication(
        current_app.config['CLIENT_ID'],
        authority=f"{current_app.config['MS_ONLINE_URL']}/{current_app.config['TENANT_ID']}",
        client_credential=current_app.config['CLIENT_SECRET'],
        token_cache=cache)


def _build_auth_url():
    return _build_msal_app().get_authorization_request_url(
        current_app.config['SCOPE'],
        redirect_uri=url_for('maildash.authorized', _external=True))


def _get_token_from_cache():
    cache = msal.SerializableTokenCache()
    if session.get('token_cache'):
        cache.deserialize(session['token_cache'])
    cca = _build_msal_app(cache)
    accounts = cca.get_accounts()
    if accounts:
        result = cca.acquire_token_silent(current_app.config['SCOPE'], account=accounts[0])
        session['token_cache'] = cache.serialize()
        return result


@maildash_bp.route('/')
def index():
    token = _get_token_from_cache()
    if not token:
        return redirect(url_for('maildash.login'))
    return redirect(url_for('maildash.dashboard'))


@maildash_bp.route('/login')
def login():
    return redirect(_build_auth_url())


@maildash_bp.route('/getAToken')
def authorized():
    cache = msal.SerializableTokenCache()
    if session.get('token_cache'):
        cache.deserialize(session['token_cache'])
    result = _build_msal_app(cache).acquire_token_by_authorization_code(
        request.args['code'],
        scopes=current_app.config['SCOPE'],
        redirect_uri=url_for('maildash.authorized', _external=True))
    if 'error' in result:
        return f"Login failure: {result['error']}"
    session['token_cache'] = cache.serialize()
    session['user'] = result.get('id_token_claims')
    return redirect(url_for('maildash.dashboard'))


@maildash_bp.route('/dashboard')
def dashboard():
    token = _get_token_from_cache()
    if not token:
        return redirect(url_for('maildash.login'))

    graph_data = requests.get(
        'https://graph.microsoft.com/v1.0/me/messages',
        headers={'Authorization': f"Bearer {token['access_token']}"},
        params={'$top': '10', '$select': 'subject,from,receivedDateTime'}
    ).json()

    return render_template(
        'dashboard.html', 
        emails=graph_data.get('value', [])
        )


@maildash_bp.route('/send', methods=['GET', 'POST'])
def send_email():
    token = _get_token_from_cache()
    if not token:
        return redirect(url_for('login'))

    if request.method == 'POST':
        to_email = request.form.get('to_email')
        subject = request.form.get('subject')
        body = request.form.get('body')

        email_msg = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "Text",
                    "content": body
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": to_email
                        }
                    }
                ]
            }
        }

        send_response = requests.post(
            'https://graph.microsoft.com/v1.0/me/sendMail',
            headers={
                'Authorization': 'Bearer ' + token['access_token'],
                'Content-Type': 'application/json'
            },
            json=email_msg
        )

        if send_response.status_code == 202:
            flash("Email sent successfully!", "success")
        else:
            flash(f"Error sending email: {send_response.text}", "danger")

        return redirect(url_for('maildash.send_email'))

    return render_template('send.html')
