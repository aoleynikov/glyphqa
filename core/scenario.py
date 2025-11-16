import json


class Scenario:
    def __init__(self, text, name=None):
        self.text = text
        self.name = name
        self.summary = None
    
    def to_steps(self, llm, template_manager):
        prompt = template_manager.scenario_to_steps(self.text)
        response = llm.process(prompt)
        return json.loads(response)
    
    def summarize(self, llm, template_manager):
        if self.summary is None:
            prompt = template_manager.scenario_summarize(self.text)
            response = llm.process(prompt)
            self.summary = response.strip()
        return self.summary

