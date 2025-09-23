class QualityMetrics:
    def __init__(self):
        self.metrics = {
            "anonymization_coverage": 0.0,
            "reidentification_risk": 0.0,
            "analysis_accuracy": 0.0
        }

    def update(self, name:str, value:float):
        if name in self.metrics:
            self.metrics[name] = value

    def get_metrics(self):
        return self.metrics
