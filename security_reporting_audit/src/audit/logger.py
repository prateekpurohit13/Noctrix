import json, time

class AuditLogger:
    def __init__(self, filepath="audit_log.jsonl"):
        self.filepath = filepath

    def log_event(self, component:str, event_type:str, details:dict):
        record = {
            "ts": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "component": component,
            "event_type": event_type,
            "details": details
        }
        with open(self.filepath,"a") as f:
            f.write(json.dumps(record)+"\n")
