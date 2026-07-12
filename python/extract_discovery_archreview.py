#!/usr/bin/env python3
"""Extract Discovery & ArchReview implementation code files."""
import re
from pathlib import Path

content_file = Path(r"c:\Users\Mike\AppData\Roaming\Code\User\workspaceStorage\9f926785ef5d9ebe9ddcfd8da23199c7\GitHub.copilot-chat\chat-session-resources\e76be132-cbf9-40a4-8d30-ebb87de24851\toolu_bdrk_01QebLMrKepiPTGR4PCJFKBU__vscode-1783660661453\content.txt")

with open(content_file, 'r') as f:
    content = f.read()

# Extract code blocks (between triple backticks)
code_blocks = re.findall(r'```python\n(.*?)\n```', content, re.DOTALL)

file_paths = [
    "aios_orchestration_core/labels/discovery_labels.py",
    "discovery_orchestrator/nodes/idea_scout.py",
    "discovery_orchestrator/langgraph_discovery_graph.py",
    "discovery_orchestrator/run_once.py",
    "arch_review_orchestrator/nodes/review.py",
    "arch_review_orchestrator/nodes/planner.py",
    "aios_orchestration_core/labels/arch_review_labels.py",
    "arch_review_orchestrator/langgraph_arch_review_graph.py",
    "arch_review_orchestrator/run_once.py",
]

print(f"Found {len(code_blocks)} code blocks, expecting {len(file_paths)}\n")

base_path = Path(".")
for i, (filepath, code) in enumerate(zip(file_paths, code_blocks), 1):
    file_path = base_path / filepath
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w') as f:
        f.write(code)
    
    print(f"{i}. Created {filepath} ({len(code)} chars)")

print("\nDone!")
