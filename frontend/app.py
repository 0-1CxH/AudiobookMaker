#!/usr/bin/env python3
"""ABM Frontend Flask Application"""

import os
import requests
from flask import Flask, render_template, request, jsonify, Response

app = Flask(__name__)

# Backend API base URL
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://127.0.0.1:5000')


def proxy_request(path, method='GET', json_data=None):
    """Proxy requests to the backend API"""
    url = f"{BACKEND_URL}{path}"
    try:
        if method == 'GET':
            resp = requests.get(url, timeout=120)
        elif method == 'POST':
            resp = requests.post(url, json=json_data, timeout=120)
        elif method == 'PUT':
            resp = requests.put(url, json=json_data, timeout=120)
        elif method == 'DELETE':
            resp = requests.delete(url, timeout=120)
        else:
            return {'error': f'Unsupported method: {method}'}, 400

        return resp.json(), resp.status_code
    except requests.exceptions.ConnectionError:
        return {'error': 'Backend server is not available', 'error_type': 'ConnectionError'}, 503
    except Exception as e:
        return {'error': str(e), 'error_type': e.__class__.__name__}, 500


# ============================================================
# Page Routes
# ============================================================

@app.route('/')
def page_projects():
    """Page 1: Project list and creation"""
    return render_template('projects.html')


@app.route('/project/<project_id>/characters')
def page_characters(project_id):
    """Page 2: Character extraction"""
    return render_template('characters.html', project_id=project_id, step=2)


@app.route('/project/<project_id>/dialogues')
def page_dialogues(project_id):
    """Page 3: Dialogue allocation"""
    return render_template('dialogues.html', project_id=project_id, step=3)


@app.route('/project/<project_id>/voice')
def page_voice(project_id):
    """Page 4: Voice design"""
    return render_template('voice.html', project_id=project_id, step=4)


@app.route('/project/<project_id>/audio')
def page_audio(project_id):
    """Page 5: Audio generation"""
    return render_template('audio.html', project_id=project_id, step=5)


# ============================================================
# API Proxy Routes
# ============================================================

@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_proxy(path):
    """Proxy all /api/* requests to the backend"""
    url = f"{BACKEND_URL}/api/{path}"
    try:
        if request.method == 'GET':
            resp = requests.get(url, timeout=120)
        elif request.method == 'POST':
            resp = requests.post(url, json=request.get_json(silent=True), timeout=120)
        elif request.method == 'PUT':
            resp = requests.put(url, json=request.get_json(silent=True), timeout=120)
        elif request.method == 'DELETE':
            resp = requests.delete(url, timeout=120)

        # Forward the response with proper content type
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for name, value in resp.raw.headers.items()
                    if name.lower() not in excluded_headers]

        return Response(resp.content, resp.status_code, headers, content_type=resp.headers.get('content-type'))
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Backend server is not available'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    host = os.environ.get('FRONTEND_HOST', '127.0.0.1')
    port = int(os.environ.get('FRONTEND_PORT', 8080))
    debug = os.environ.get('FRONTEND_DEBUG', 'true').lower() == 'true'

    print(f"Starting ABM Frontend on http://{host}:{port}")
    print(f"Backend URL: {BACKEND_URL}")

    app.run(host=host, port=port, debug=debug)
