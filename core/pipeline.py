class PipelineContext:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def add_result(self, stage_name, result):
        if not hasattr(self, 'results'):
            self.results = {}
        self.results[stage_name] = result


class PipelineStage:
    def __init__(self, name, next_stage=None):
        self.name = name
        self.next_stage = next_stage
    
    def execute(self, context):
        result = self.process(context)
        context.add_result(self.name, result)
        
        if self.next_stage:
            return self.next_stage.execute(context)
        return context
    
    def process(self, context):
        raise NotImplementedError('Subclasses must implement process method')
    
    def set_next(self, stage):
        self.next_stage = stage
        return stage

