import shutil
import argparse
from pathlib import Path

def create_task(name: str, description: str):
    task_dir = Path('tasks') / name
    task_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy template files
    template_dir = Path('template')
    for f in template_dir.iterdir():
        shutil.copy(f, task_dir / f.name)
    
    # Replace [TaskName] placeholder in generate.py
    generate_py = task_dir / 'generate.py'
    content = generate_py.read_text()
    class_name = name.strip().replace(' ', '')  # Simple class name from task name
    content = content.replace('TaskName', class_name)
    content = content.replace('[TASK NAME]', name)
    content = content.replace('[BRIEF DESCRIPTION]', description)
    generate_py.write_text(content)
    
    print(f"✓ Created task: tasks/{name}/")
    print(f"  Next steps:")
    print(f"  1. Implement generate() in tasks/{name}/generate.py")
    print(f"  2. Fill in metarubrics.json templates")
    print(f"  3. Fill in config.json difficulty parameters")
    print(f"  4. Run: python evaluate.py --task {name} --validate-only")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True)
    parser.add_argument('--description', default='')
    args = parser.parse_args()
    create_task(args.name, args.description)