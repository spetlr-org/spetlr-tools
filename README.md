# spetlr-tools

## Table of Contents

- [Description](#description)
- [Purpose of spetlr-tools](#purpose-of-spetlr-tools)
- [Installation](#installation)
- [Development Notes](#development-notes)
- [Testing](#testing)
- [General Project Info](#general-project-info)
- [Contributing](#contributing)
- [Build Status](#build-status)
- [Releases](#releases)
- [Contact](#contact)

## Description
SPETLR-tools is a library that provides a set of tools for working with Databricks Lakehouses. These tools include test fixtures and development utilities that are not part of the runtime tools in [SPETLR](https://github.com/spetlr-org/spetlr).


Visit the official SPETLR webpage: [https://spetlr.com/](https://spetlr.com/)


## Purpose of SPETLR-tools

SPETLR-tools is designed to support SPETLR in various scenarios, including:

* Test tools in pytest:
    * Examples: Dataframe validation checks, Data format checking, ...
* Helpers for investigating data:
    * Examples: Extract schema from binary encoded columns, Get the difference between two dataframes , ...
* SPETLR-tools CLI:
    * Examples: Submit pytests to Databricks cluster, Automated Azure Token extraction, ... 

## SPETLR-tools vs. SPETLR

* SPETLR-tools: Tested in a Python interpreter and per january 2024 also integration tested using on-cluster job tests.
* SPETLR-tools: Github workflow have an very simple Azure Deployment
* SPETLR: Fully unit and integration tested - library ready for production use
* SPETLR-tools: Supports deployment and testing
    * Use only in `test_requirements.txt`

# Installation

Install SPETLR from PyPI: 

[![PyPI version](https://badge.fury.io/py/spetlr-tools.svg)](https://pypi.org/project/spetlr-tools/)
[![PyPI](https://img.shields.io/pypi/dm/spetlr-tools)](https://pypi.org/project/spetlr-tools/)
```    
pip install spetlr-tools
```

# Development Notes

To prepare for development, please install following additional requirements:
 - Java 8
 - `pip install -r test_requirements.txt`

Then install the package locally:

    python setup.py develop

## Testing

### Local tests
After installing the dev-requirements, execute tests by running:

    pytest tests

These tests are located in the `./tests/unit` folder and only require a Python interpreter. Pull requests will not be accepted if these tests do not pass. If you add new features, please include corresponding tests.

### CLI and Cluster tests
During the pre-integration workflow (`.gitub/workflows/pre-integration.yml`) spetlr-tool supported CLI are (should) be tested. 

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