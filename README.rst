darca-yaml
==========

A lightweight YAML utility library with validation support using Cerberus, designed for simplicity and composability in structured Python projects.

.. image:: https://img.shields.io/pypi/v/darca-yaml
    :target: https://pypi.org/project/darca-yaml/
    :alt: PyPI

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    :alt: Black code style

Overview
--------

**darca-yaml** provides utilities for:

- 📖 Loading and saving YAML files
- ✅ Validating YAML content with Cerberus
- 🔗 Integrated exception handling (`darca-exception`)
- 📄 File handling via `darca-file-utils`
- 🧪 100% test coverage with Pytest and CI integration

Installation
------------

.. code-block:: bash

    pip install darca-yaml

Usage
-----

.. code-block:: python

    from darca_yaml.yaml_utils import YamlUtils

    schema = {"name": {"type": "string"}, "enabled": {"type": "boolean"}}

    data = YamlUtils.load_yaml_file("config.yaml")
    YamlUtils.validate_yaml(data, schema)
    YamlUtils.save_yaml_file("output.yaml", data, validate=True, schema=schema)

Development Setup
-----------------

Clone the repo and install dependencies:

.. code-block:: bash

    git clone https://github.com/roelkist/darca-yaml
    cd darca-yaml
    make install

Run checks before committing:

.. code-block:: bash

    make check

Run individual targets (faster iteration):

.. code-block:: bash

    make format
    make test
    make precommit
    make docs

Contribution Guide
------------------

We welcome contributions via **pull requests** to `main`.  
Please see the `CONTRIBUTING.rst` file for detailed instructions.

License
-------

MIT

