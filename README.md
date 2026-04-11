![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Pandas](https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/numpy-%23013243.svg?style=for-the-badge&logo=numpy&logoColor=white)
![SciPy](https://img.shields.io/badge/SciPy-%230C55A5.svg?style=for-the-badge&logo=scipy&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-%23ffffff.svg?style=for-the-badge&logo=Matplotlib&logoColor=black)
![LiteLLM](https://img.shields.io/badge/LiteLLM-blueviolet?style=for-the-badge)

# Physics analysis benchmark 📊

*A framework for building contamination-free scientific benchmarks for LLM evaluation with deterministically generated rubrics.*

## What is this?

XXXX is a framework for evaluating LLMs on realistic scientific analysis workflows using procedurally generated tasks with perfectly synchronized rubrics.

Every run produces fresh multimodal instances (plots, CSVs, data tables) from a controlled generative process. The key innovation is source-grounded metarubrics: rubric templates that are automatically populated directly from the generated ground truth. This guarantees that evaluation criteria are always perfectly aligned with the task data — eliminating rubric drift by construction.

Because tasks are generated from a fixed distribution controlled by difficulty parameters and random seeds, the framework supports statistically rigorous evaluation. Multiple independent seeds at the same difficulty level allow treating each run as an independent trial, enabling proper confidence intervals, per-rubric breakdowns, and robust model comparisons.


## The core idea

Traditional benchmarks rely on fixed test sets that leak into training data, becoming contaminated or saturated. Common solutions — hiding test sets or constantly adding new questions — either sacrifice transparency or require unsustainable effort.

Procedural generation solves leakage by creating fresh instances every run. But it introduces a new problem: keeping rubrics aligned with dynamically generated data, especially in multi-step scientific tasks.

Our solution: use the same generating process that creates the task data to also instantiate the rubrics. We call these templates **metarubrics**. Every rubric criterion is mathematically guaranteed to match the generated instance  by construction, not by validation.


## Quick start


## Results


## How it works


## Contributing tasks


## Citation
