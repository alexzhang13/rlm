
---

<h2 align="center">
Recursive Language Models
</h2>

## Overview
Recursive Language Models (RLMs) are a task-agnostic inference paradigm for language models (LMs) to handle near unbounded contexts by enabling the LM to *programmatically* examine, decompose, and recursively call itself over its input. 

## Installation
```
pip install rlm
```
To install the latest from `main`:
```
pip install git+https://github.com/alexzhang13/rlm.git
```

## Local Setup
```
curl -LsSf https://astral.sh/uv/install.sh | sh
uv init && uv venv --python 3.12  # change version as needed
```


## Overview
General plug-and-play inference for RLMs