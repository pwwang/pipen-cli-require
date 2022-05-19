# pipen-cli-run

A pipen cli plugin to run a process or a pipeline

## Install

```shell
pip install -U pipen-cli-run
```

## Usage

### Register a namespace

`pyproject.toml`
```toml
[tool.poetry.plugins.pipen_cli_run]
ns = "yourpackage.ns"
```

`ns` should be a module where you define you processes/pipelines
