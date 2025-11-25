import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain.schema import HumanMessage, SystemMessage

load_dotenv()


class LangChainLLM:
    def __init__(self, model, api_key=None, temperature=0):
        self.model = model
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError('OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.')
        
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=temperature
        )
    
    def process(self, prompt, system_prompt=None):
        messages = []
        
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        
        messages.append(HumanMessage(content=prompt))
        
        response = self.llm.invoke(messages)
        return response.content
    
    def process_json(self, prompt, system_prompt=None):
        response = self.process(prompt, system_prompt)
        response = response.strip()
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            raise ValueError(f'Failed to parse JSON response: {e}\nResponse: {response[:500]}')
    
    def process_with_template(self, template_text, **kwargs):
        prompt_template = PromptTemplate.from_template(template_text)
        prompt = prompt_template.format(**kwargs)
        return self.process(prompt)
    
    def process_with_chat_template(self, system_template, user_template, **kwargs):
        system_prompt = SystemMessage(content=system_template.format(**kwargs))
        user_prompt = HumanMessage(content=user_template.format(**kwargs))
        response = self.llm.invoke([system_prompt, user_prompt])
        return response.content


