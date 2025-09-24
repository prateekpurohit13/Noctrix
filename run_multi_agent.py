import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from src.document_processor.main import process_input
from src.multi_agent_system import (
    AgentOrchestrator, 
    DocumentUnderstandingAgent,
    # PIIDetectionAgent,
    # SecurityEntityAgent, 
    # RelationshipMappingAgent,
    AnalysisAgent,
    SecurityAssessmentAgent,
    AnonymizationAgent,
    ReportingAgent
)
from src.reporting.utils import export_pdf_from_md 

def progress_callback(stage: str, progress: float, message: str):
    print(f"  -> [{progress:5.1f}%] {stage}: {message}")


def main():   
    if len(sys.argv) != 2:
        print("Usage: python run_multi_agent.py <path_to_file_or_zip>")
        sys.exit(1)   
    input_path = Path(sys.argv[1])   
    if not input_path.exists():
        print(f"Error: File '{input_path}' not found")
        sys.exit(1)
    
    print("Starting Multi-Agent Document Processing System")
    print(f"   Input: {input_path}")
    print(f"   Architecture: 5-Agent AI Pipeline")
    print("-" * 50)
    
    try:
        print("--- Stage 1: Document Processing (DOM Creation) ---")
        doms = process_input(input_path)
        
        if not doms:
            print("No valid documents were processed to create a DOM.")
            sys.exit(1)
        
        print(f"DOM Creation Complete. Found {len(doms)} document(s) to analyze.")
        print("-" * 50)

        for i, dom in enumerate(doms):
            print(f"\n--- Analyzing Document {i+1}/{len(doms)}: {dom.file_name} ---")
            print("--- Stage 2: Multi-Agent System Initialization ---")
            orchestrator = AgentOrchestrator(max_workers=3)
            agents = [
            DocumentUnderstandingAgent(),
            AnalysisAgent(),
            SecurityAssessmentAgent(),
            AnonymizationAgent(),
            ReportingAgent()
        ]
            
            for agent in agents:
                orchestrator.register_agent(agent)
            print(f"Registered {len(agents)} agents.")
            print("\n--- Stage 3: Multi-Agent Pipeline Execution ---")
            output_json = orchestrator.process_document(dom)
            print("\n--- Stage 4: Finalizing and Saving Results ---")
            pipeline_status = output_json["output"].get("pipeline_status", "PARTIAL")
            total_entities_found = output_json["output"].get("total_entities_found", "N/A")
            print(f"  -> Pipeline Status: {pipeline_status}")
            print(f"  -> Total Entities Found: {total_entities_found}")
            file_name_stem = Path(dom.file_name).stem
            output_dir = Path("data/output")
            os.makedirs(output_dir, exist_ok=True)
            # Save the main JSON output
            json_output_path = output_dir / f"{file_name_stem}_multi_agent.json"
            import json
            with open(json_output_path, 'w', encoding='utf-8') as f:
                json.dump(output_json, f, indent=2, ensure_ascii=False, default=str)
            print(f"Full JSON results saved to: {json_output_path}")

            md_report = output_json.get("output", {}).get("markdown_security_report", "")
            if md_report:
                pdf_path = output_dir / f"{file_name_stem}_security_report.pdf"
                export_pdf_from_md(md_report, str(pdf_path))
                print(f"Final PDF report saved to: {pdf_path}")
            
            print("-" * 50)

        print("\n\nAll documents processed successfully!")
        return 0
        
    except Exception as e:
        print(f"A critical error occurred during batch processing: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

def progress_callback(stage: str, progress: float, message: str):
    print(f"  -> [{progress:5.1f}%] {stage}: {message}")

if __name__ == "__main__":
    sys.exit(main())