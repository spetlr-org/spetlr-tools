# spetlr-tools
This library is a set of tools for working with Databricks Lakehouses.
These libraries contain test fixtures and development tools 
that are not part of the runtime tools in [SPETLR](https://github.com/spetlr-org/spetlr).


Visit SPETLR official webpage: [https://spetlr.com/](https://spetlr.com/)


## What is the purpose of SPETLR-tools?

Support SPETLR in scenarious like:

* Test tools in pytests
    * Examples: Dataframe validation checks, Data format checking, ...
* Helpers for investigating data
    * Examples: Extract schema from binary encoded columns, Get the difference between two dataframes , ...
* SPETLR-tools cli
    * Examples: Submit pytests to Databricks cluster, Automated Azure Token extraction, ... 

## SPETLR vs. SPETLR-tools

* SPETLR-tools: Only tested in python interpreter
* SPETLR-tools: Github workflow has no Azure Deployment
    * Thus, no integration tests on clusters
* SPETLR: Is fully unit and integration tested meant for production use
* SPETLR-tools: Supports deployment and testing
    * Use only in `test_requirements.txt`

# Installation

Install SPETLR it from PyPI: 
[![PyPI version](https://badge.fury.io/py/spetlr-tools.svg)](https://pypi.org/project/spetlr-tools/)
[![PyPI](https://img.shields.io/pypi/dm/spetlr-tools)](https://pypi.org/project/spetlr-tools/)
```    
pip install spetlr-tools
```

# Development Notes

To prepare for development, please install these additional requirements:
 - Java 8
 - `pip install -r test_requirements.txt`

Then install the package locally

    python setup.py develop

## Testing

### Local tests
After installing the dev-requirements, execute tests by running:

    pytest tests

These tests are located in the `./tests/unot` folder and only require a Python interpreter. Pull requests will not be accepted if these tests do not pass. If you add new features, please include corresponding tests.



# General Project Info
[![Github top language](https://img.shields.io/github/languages/top/spetlr-org/spetlr-tools)](https://github.com/spetlr-org/spetlr-tools)
[![Github stars](https://img.shields.io/github/stars/spetlr-org/spetlr-tools)](https://github.com/spetlr-org/spetlr-tools)
[![Github forks](https://img.shields.io/github/forks/spetlr-org/spetlr-tools)](https://github.com/spetlr-org/spetlr-tools)
[![Github size](https://img.shields.io/github/repo-size/spetlr-org/spetlr-tools)](https://github.com/spetlr-org/spetlr-tools)
[![Issues Open](https://img.shields.io/github/issues/spetlr-org/spetlr-tools.svg?logo=github)](https://github.com/spetlr-org/spetlr-tools/issues)
[![PyPI spetlr badge](https://img.shields.io/pypi/v/spetlr-tools)](https://pypi.org/project/spetlr-tools/)


# Contributing

Feel free to contribute to SPETLR-tools. Any contributions are appreciated - not only new features, but also if you find a way to improve SPETLR-tools. 

If you have a suggestion that can enhance SPETLR-tools, please fork the repository and create a pull request. Alternatively, you can open an issue with the "enhancement" tag.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/NewSPETLRToolsFeature`)
3. Commit your Changes (`git commit -m 'Add some SEPTLRToolsFeature'`)
4. Push to the Branch (`git push origin feature/NewSPETLRToolsFeature`)
5. Open a Pull Request


# Build Status

[![Post-Integration](https://github.com/spetlr-org/spetlr-tools/actions/workflows/post-integration.yml/badge.svg)](https://github.com/spetlr-org/spetlr-tools/actions/workflows/post-integration.yml)


# Releases
Releases to PyPI is an Github Action which needs to be manually triggered. 

[![Release](https://github.com/spetlr-org/spetlr-tools/actions/workflows/release.yml/badge.svg)](https://github.com/spetlr-org/spetlr-tools/actions/workflows/release.yml)
[![PyPI spetlr badge](https://img.shields.io/pypi/v/spetlr-tools)](https://pypi.org/project/spetlr-tools/)

# Contact

For any inquiries, please use the [SPETLR Discord Server](https://discord.gg/p9bzqGybVW).