import os
import openai
import json
import re

def single_llm_request(**kwargs):
    """使用OpenAI SDK进行LLM请求"""
    api_key = kwargs.get('api_key') or os.environ.get('LLM_API_KEY')
    api_base = kwargs.get('api_url') or os.environ.get('LLM_API_URL')

    client = openai.OpenAI(
        api_key=api_key,
        base_url=api_base,
    )

    response = client.chat.completions.create(
        model=kwargs['model'],
        messages=[
            {"role": "user", "content": kwargs['prompt']}
        ],
        n=1
    )

    return response.choices[0].message.content

def extract_json(s):
    json_data = None
    try:
        # Try to extract JSON content from code block
        if "```json" in s and "```" in s.split("```json", 1)[1]:
            json_content = s.split("```json", 1)[1].split("```")[0].strip()
        elif "<json>" in s and "</json>" in s.split("</json>", 1)[1]:
            json_content = s.split("</json>", 1)[1].split("</json>")[0].strip()
        elif "```" in s:
            # Try to extract from any code block
            json_content = s.split("```", 2)[1].strip()
        else:
            json_content = s.strip()
        
        # Safely parse JSON
        json_data = json.loads(json_content)
        
        if not isinstance(json_data, dict):
            json_data = {"result": json_data}
    except json.JSONDecodeError:
        # if can not decode, try extract using regex
        json_pattern = r'\{[^{}]*\}'
        matches = re.findall(json_pattern, s)
        if matches:
            json_data = json.loads(matches[0])
        else:
            # if everything fails, create a dict of str s
            json_data = {"response": s}
    return json_data
