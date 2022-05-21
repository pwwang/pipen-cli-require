# pipen-cli-run

Checking the requirements for processes of a pipeline

## Install

```shell
pip install -U pipen-cli-require
```

## Usage

### Defining requirements of a process

```python
# pipeline.py
from pipen import Pipen, Proc

class P1(Proc):
    """Process 1

    Requires:
        - name: pipen
          message: Run `pip install -U pipen` to install
          check: |
            {{proc.lang}} -c "import pipen"
        - name: liquidpy
          message: Run `pip install -U liquidpy` to install
          check: |
            {{proc.lang}} -c "import liquid"
        - name: nonexist
          message: Run `pip install -U nonexist` to install
          check: |
            {{proc.lang}} -c "import nonexist"
    """
    input = "a"
    output = "outfile:file:out.txt"
    lang = "python"

# Setup the pipeline
# Must be outside __main__
# Or define a function to return the pipeline
pipeline = Pipen(...)

if __name__ == '__main__':
    # Pipeline must be executed with __main__
    pipeline.run()
```

## Checking the requirements via the CLI

```shell
> pipen require -v -n 2 tests/example_pipeline.py:example_pipeline

Checking requirements for pipeline: EXAMPLE_PIPELINE
└── P1: Process 1
    ├── ✔️ pipen
    ├── ✔️ liquidpy
    └── x nonexist: Run `pip install -U nonexist` to install
        └── Traceback (most recent call last):
              File "<string>", line 1, in <module>
            ModuleNotFoundError: No module named 'nonexist'
```
