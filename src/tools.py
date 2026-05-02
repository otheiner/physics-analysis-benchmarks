from pathlib import Path

# Extract allowed libraries from requirements.txt
def _load_sandbox_libraries() -> str:
    """Extract package names from sandbox/requirements.txt."""
    req_path = Path(__file__).parent.parent / 'sandbox' / 'requirements.txt'
    
    libraries = []
    for line in req_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            # Strip version pin — numpy==1.26.4 → numpy
            package = line.split('==')[0].split('>=')[0].split('<=')[0]
            libraries.append(package)
    
    return ', '.join(libraries)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_python",
            "description": (
                "Execute a Python script to analyse the task data. "
                "Input files are available in the current directory. "
                f"Available libraries: {_load_sandbox_libraries()}. "
                "Print your results — stdout is returned to you."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Complete Python script to execute."
                    }
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": (
                "Run a shell command in the workspace for quick data inspection. "
                "Allowed commands: grep, sed, awk, find, head, tail, cat, wc, sort, uniq, cut, ls, file. "
                "Supports pipes (|), logical operators (&& / ||), semicolons (;), and regex patterns. "
                "Paths are relative to the workspace directory."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to run, e.g. 'head -5 data.csv' or 'grep pattern file.txt'."
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": (
                "Write text content to a file in the workspace. "
                "Use this to save intermediate results, notes, or small data files. "
                "Paths are relative to the workspace directory. "
                "Overwrites the file if it already exists."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file relative to the workspace."
                    },
                    "content": {
                        "type": "string",
                        "description": "Text content to write."
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Read a text or CSV file from the workspace and return its contents. "
                "Use this to inspect input data before writing analysis code. "
                "Paths are relative to the workspace directory."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file relative to the workspace."
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "view_image",
            "description": (
                "Render an image file into your context so you can inspect it. "
                "Use this to view plots you have saved or input image files. "
                "Paths are relative to the workspace directory."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the image file relative to the workspace."
                    }
                },
                "required": ["path"]
            }
        }
    }
]