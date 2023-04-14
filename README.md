# pipen-cli-require

Checking the requirements for processes of a [pipen][1] pipeline

## Install

```shell
pip install -U pipen-cli-require
```

## Usage

### Defining requirements of a process

```python
# example_pipeline.py
from pipen import Pipen, Proc

class P1(Proc):
    """Process 1

    Requires:
        pipen: Run `pip install -U pipen` to install
          - check: |
            {{proc.lang}} -c "import pipen"
        liquidpy: Run `pip install -U liquidpy` to install
          - check: |
            {{proc.lang}} -c "import liquid"
        nonexist: Run `pip install -U nonexist` to install
          - check: |
            {{proc.lang}} -c "import nonexist"
        conditional:
          - if: {{envs.require_conditional}}
          - check:
            {{proc.lang}} -c "import optional"

    """
    input = "a"
    output = "outfile:file:out.txt"
    envs = {"require_conditional": False}
    lang = "python"

# Setup the pipeline
# Must be outside __main__
# Or define a function to return the pipeline
class Pipeline(Pipen):
    starts = P1


if __name__ == '__main__':
    # Pipeline must run with __main__
    Pipeline().run()
```

### Parsing process requirements using API

```python
from pipen_cli_require import parse_proc_requirements


def parse_proc_requirements(
    proc: Type[Proc]
) -> Tuple[OrderedDiot, OrderedDiot]:
    """Parse the requirements of a process

    Args:
        proc: The process class

    Returns:
        A tuple of two OrderedDiot's.
        The first one is the annotated sections by pipen_annotate
        The second one is the requirements. The key is the name of the
            requirement, the value is a dict with message, check and if_ keys.
    """
```

## Checking the requirements via the CLI

```shell
> pipen require --verbose --ncores 2 example_pipeline.py:pipeline

Checking requirements for pipeline: PIPEN-0
│
└── P1: Process 1
    ├── ✅ pipen
    ├── ✅ liquidpy
    ├── ❎ nonexist: Run `pip install -U nonexist` to install
    │   └── Traceback (most recent call last):
    │         File "<string>", line 1, in <module>
    │       ModuleNotFoundError: No module named 'nonexist'
    │
    └── ⏩ conditional (skipped by if-statement)
```

## Checking requirements with runtime arguments

For example, when I use a different python to run the pipeline:

Add this to the head of `example_pipeline.py`:

```python
import pipen_args
```

See also `tests/pipen_args_pipeline.py`

Then specify the path of the python to use:

```shell
pipen require example_pipeline.py:pipeline --P1.lang /path/to/another/python
```

[1]: https://github.com/pwwang/pipen
