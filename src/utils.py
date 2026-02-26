import os
import requests

def llm_request_by_curl(**kwargs):
    api_url = kwargs.get('api_url') or os.environ.get('LLM_API_URL')
    api_key = kwargs.get('api_key') or os.environ.get('LLM_API_KEY')
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "messages": [{"role": "user", "content": kwargs['prompt']}],
        "model": kwargs['model'],
        "stream": kwargs.get('stream', False),
        **kwargs.get('extra_params', {})
    }
    response = requests.post(api_url, headers=headers, json=payload, timeout=180)
    response.raise_for_status()
    response_data = response.json()
    return response_data['choices'][0]['message']['content']

