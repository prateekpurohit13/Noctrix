from jinja2 import Environment, FileSystemLoader
import os

class ReportGenerator:
    def __init__(self, template_dir:str = None):
        if template_dir is None:
            template_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def generate_report(self, context:dict) -> str:
        sections = ["executive_summary","technical_details","remediation","compliance"]
        output = []
        for section in sections:
            template = self.env.get_template(f"{section}.j2")
            output.append(template.render(context))
        return "\n\n".join(output)
