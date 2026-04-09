## Contributing a task

1. You need: domain knowledge + Python simulation code
2. Run: python new_task.py --name your_task_name
3. Implement: generate_task() in tasks/your_task/generate.py
4. Fill in: metarubrics.json and config.json
5. Test: python evaluate.py --task your_task --validate-only
6. Submit: pull request