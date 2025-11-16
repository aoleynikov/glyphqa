import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class OpenAILLM:
    def __init__(self, model, api_key=None):
        self.model = model
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError('OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.')
        
        client_kwargs = {'api_key': api_key}
        self.client = OpenAI(**client_kwargs)
    
    def process(self, prompt):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt}]
        )
        return response.choices[0].message.content

