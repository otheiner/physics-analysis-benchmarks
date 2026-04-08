"""
evaluate.py — CLI entry point for the benchmark evaluation pipeline.

Usage:
    python evaluate.py --task your_task_name --model ollama/llama3.2
    python evaluate.py --all --model ollama/llama3.2 --seeds 0 1 2 3 4
    python evaluate.py --task your_task_name --validate-only
    python evaluate.py --list
"""

import argparse
import importlib
import inspect
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.task import Task
from src.evaluator import Evaluator


# ─────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────

def discover_tasks(tasks_dir='tasks') -> dict:
    """Autodiscover all Task subclasses in the tasks/ folder."""
    discovered = {}
    
    for task_folder in sorted(Path(tasks_dir).iterdir()):
        if not task_folder.is_dir():
            continue
        generate_file = task_folder / 'generate.py'
        if not generate_file.exists():
            continue
        
        module_path = f"tasks.{task_folder.name}.generate"
        module = importlib.import_module(module_path)
        
        task_classes = [
            obj for name, obj
            in inspect.getmembers(module, inspect.isclass)
            if issubclass(obj, Task)
            and obj is not Task
            and obj.__module__ == module_path
        ]
        
        if len(task_classes) == 0:
            print(f"No Task subclass found in {generate_file}")
            continue
        
        if len(task_classes) > 1:
            print(f"⚠  Multiple Task subclasses in {generate_file} — using first")
        
        discovered[task_folder.name] = task_classes[0]
    
    return discovered


def list_tasks(tasks: dict):
    """Print all discovered tasks."""
    print("\nDiscovered tasks:")
    for name, cls in tasks.items():
        print(f"  ✓ {name} → {cls.__name__}")
    print()


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description='Evaluate LLMs on physics benchmark tasks.'
    )
    parser.add_argument('--task',          type=str,
                        help='Task folder name')
    parser.add_argument('--all',           action='store_true',
                        help='Run all discovered tasks')
    parser.add_argument('--list',          action='store_true',
                        help='List all discovered tasks and exit')
    parser.add_argument('--model',         type=str,
                        default='ollama/llama3.2',
                        help='Model to evaluate')
    parser.add_argument('--judge',         type=str,
                        default='gemini/gemini-pro',
                        help='Model to use as judge for extraction')
    parser.add_argument('--difficulty',    type=str,
                        default='medium',
                        choices=['easy', 'medium', 'hard'])
    parser.add_argument('--seeds',         type=int, nargs='+',
                        default=[0],
                        help='Random seeds for multiple runs')
    parser.add_argument('--validate-only', action='store_true',
                        help='Generate data and validate rubrics without running model')
    return parser.parse_args()


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    args = parse_args()
    tasks = discover_tasks()
    
    if args.list:
        list_tasks(tasks)
        return
    
    evaluator = Evaluator()
    
    if args.all:
        task_names = list(tasks.keys())
    elif args.task:
        if args.task not in tasks:
            print(f"✗ Task '{args.task}' not found.")
            list_tasks(tasks)
            return
        task_names = [args.task]
    else:
        print("Specify --task or --all. Use --list to see available tasks.")
        return
    
    for task_name in task_names:
        task_cls = tasks[task_name]
        for seed in args.seeds:
            evaluator.run(
                task_cls=task_cls,
                task_name=task_name,
                difficulty=args.difficulty,
                eval_model=args.model,
                judge_model=args.judge,
                seed=seed,
                validate_only=args.validate_only
            )


if __name__ == "__main__":
    main()