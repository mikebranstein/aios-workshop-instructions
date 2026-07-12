#!/usr/bin/env python3
"""Extract generated code files from temp content."""
import re
from pathlib import Path

# Read the generated content file
content_file = Path(r"c:\Users\Mike\AppData\Roaming\Code\User\workspaceStorage\9f926785ef5d9ebe9ddcfd8da23199c7\GitHub.copilot-chat\chat-session-resources\e76be132-cbf9-40a4-8d30-ebb87de24851\toolu_bdrk_01Q5rsh8zMAFonf47PuLvonG__vscode-1783660661361\content.txt")

with open(content_file, 'r') as f:
    content = f.read()

# Extract all python code blocks
file_pattern = r'File \d+: ([^\n]+)\n\n```python\n(.*?)\n```'
matches = list(re.finditer(file_pattern, content, re.DOTALL))

print(f"Found {len(matches)} code blocks\n")

base_path = Path(".")
for i, match in enumerate(matches, 1):
    filepath = match.group(1).strip()
    code = match.group(2)
    
    # Create the file path
    file_path = base_path / filepath
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the file
    with open(file_path, 'w') as f:
        f.write(code)
    
    print(f"{i}. Created {filepath} ({len(code)} chars)")

print("\nDone!")
