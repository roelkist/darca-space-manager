darca-space-manager
===================

A local storage abstraction layer for managing logical spaces using the filesystem and YAML metadata.

|Build Status| |License|

Overview
--------

**darca-space-manager** provides a clean interface to create, delete, and manage isolated storage "spaces" on disk, each optionally enriched with YAML-based metadata. It is designed for modular integration with other DARCA services and utilities.

Maintained by `Roel Kist <https://github.com/roelkist>`_

Features
--------

- ✅ Create and delete isolated named spaces
- 🗃️ Store and retrieve structured YAML metadata
- 🔍 List and count all active spaces
- 📁 Filesystem-based, no database required
- 🧪 100% test coverage and automated CI

Installation
------------

.. code-block:: bash

   git clone https://github.com/roelkist/darca-space-manager.git
   cd darca-space-manager
   make install

Quick Start
-----------

.. code-block:: python

   from darca_space_manager.space_manager import SpaceManager

   manager = SpaceManager()
   manager.create_space("demo", metadata={"purpose": "testing"})

   print(manager.space_exists("demo"))           # True
   print(manager.get_space_metadata("demo"))     # {'purpose': 'testing'}
   print(manager.list_spaces())                  # ['demo']
   manager.delete_space("demo")

Development
-----------

Run the full test suite and all linters:

.. code-block:: bash

   make test     # Run tests with coverage
   make check    # Run all quality tools (lint, type check, etc.)
   make format   # Auto-format code with Black + Ruff

Project Layout
--------------

.. code-block::

   src/darca_space_manager/
   ├── space_manager.py       # Main logic
   ├── config.py              # Directory configuration
   └── __version__.py         # Version info

   tests/                     # Pytest suite
   Makefile                   # Developer workflow commands

License
-------

This project is licensed under the MIT License. See ``LICENSE`` for full terms.

.. |Build Status| image:: https://github.com/roelkist/darca-space-manager/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/roelkist/darca-space-manager/actions
.. |License| image:: https://img.shields.io/badge/license-MIT-blue.svg
   :target: https://opensource.org/licenses/MIT
