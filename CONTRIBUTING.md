## Contributing a task

This project started as a personal passion project. If you feel motivated to contribute a task from your domain, I would be happy to help.

Fork the repository and scaffold a new task:

```bash
python new_task.py --name my_task --author "Your Name"
```

Implement `generate_task()` in `tasks/my_task/generate.py` and fill in `tasks/my_task/config.json` and `tasks/my_task/metarubrics.json`. The framework handles everything else.

Validate without API calls:

```bash
python run.py --task my_task --validate-only
```

Then open a pull request. Any scientific process with a simulatable generating distribution can become a task — physics, mathematics, chemistry, biology, climate science, and beyond. Tasks in the repo starting with underscore are skipped for benchmarking (unless explicitly requested in `run.py` by `--tasks <_task_name>`) but they are minimal working examples that can be used as a reference.