import json


class Scenario:
    def __init__(self, text):
        self.text = text
    
    def to_steps(self, llm, template_manager):
        prompt = template_manager.scenario_to_steps(self.text)
        response = llm.process(prompt)
        return json.loads(response)

