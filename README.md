![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Pandas](https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/numpy-%23013243.svg?style=for-the-badge&logo=numpy&logoColor=white)
![SciPy](https://img.shields.io/badge/SciPy-%230C55A5.svg?style=for-the-badge&logo=scipy&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-%23ffffff.svg?style=for-the-badge&logo=Matplotlib&logoColor=black)
![LiteLLM](https://img.shields.io/badge/LiteLLM-blueviolet?style=for-the-badge)

# Physics analysis benchmark 📊

*A framework for building contamination-free scientific benchmarks for LLM evaluation with deterministically generated rubrics.*

## What is this?

XXXX is a framework for procedurally generated scientific tasks grounded in real data analysis workflows. Every run produces fresh instances with mathematically guaranteed correct rubrics — making benchmark contamination structurally impossible while keeping evaluation criteria strictly aligned with the generated data.

Task generation is randomised but fully reproducible: fixing a random seed produces identical instances, allowing results to be traced back to exact inputs. Multiple seeds enable treating LLM evaluation as a series of independent trials — amenable to standard statistical methods such as confidence intervals and hypothesis testing. This allows distinguishing genuine model capability from response variability, and enables statistically principled model comparison.


## The core idea

Traditional benchmarks store fixed evaluation questions, which can leak into model training data — rendering the benchmark obsolete. This is typically addressed either by withholding evaluation datasets or by continuously adding new questions. The former sacrifices transparency; the latter requires significant ongoing effort and prevents objective comparison across benchmark versions.

Procedural generation offers an alternative: tasks are generated fresh each run, so there is nothing to leak. However, this introduces a new challenge — keeping evaluation rubrics aligned with the generated data. For tasks with a single final answer this is straightforward, but multi-step scientific analyses require granular rubrics that check intermediate results. LLM-generated rubrics partially address this, but introduce rubric drift: the grading criteria are no longer guaranteed to match the generated data.

Our approach resolves this with a simple observation: the same generating distribution used to produce task instances can be used to populate rubric templates deterministically. We call these templates metarubrics. Because metarubrics are instantiated from the same simulation that produces the input data, their correctness is guaranteed by construction — no manual validation or LLM generation required. Metarubrics also naturally support tasks with repeated reasoning steps, such as extracting measurements from each object in a dataset, where the number of rubric criteria scales automatically with the generated data.





## Quick start


## Results


## How it works


## Contributing tasks


## Citation