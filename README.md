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

Traditional benchmarks rely on fixed test sets that can leak into training data, quickly becoming saturated or contaminated. Common solutions — hiding test sets or constantly creating new questions — either sacrifice transparency or require unsustainable maintenance effort.

Procedural generation solves the leakage problem by creating fresh instances on every run. However, it introduces a new challenge: how do you keep evaluation rubrics aligned with dynamically generated data, especially in complex multi-step scientific tasks? Most approaches either use static rubrics or ask an LLM to generate rubrics on the fly (which introduces inconsistency and hallucination).

Our solution is simpler and more robust: use the same generating process that creates the task data to also instantiate the rubrics. We define lightweight metarubrics — templates with explicit source pointers to the ground truth. These templates are automatically populated with concrete values from the simulation, ensuring that every rubric criterion is mathematically guaranteed to be correct and perfectly matched to the instance.

This approach naturally scales to tasks with variable numbers of steps (e.g., extracting measurements from 10 vs 100 objects) and provides a clean foundation for statistical aggregation across seeds.


## Quick start


## Results


## How it works


## Contributing tasks


## Citation