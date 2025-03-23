Contributing to darca-space-manager
===================================

Thanks for your interest in contributing to **darca-space-manager** — a project by `Roel Kist <https://github.com/roelkist>`_.

We welcome issues, pull requests, questions, suggestions, and other contributions from the community.

Getting Started
---------------

Clone the project and set up the development environment:

.. code-block:: bash

   git clone https://github.com/roelkist/darca-space-manager.git
   cd darca-space-manager
   make install

This will create a virtual environment and install all dependencies needed for development, testing, and formatting.

Workflow
--------

- 🔍 Open an issue first for bugs or major features
- ✅ Fork, branch, and develop your changes
- 📦 Run tests and checks locally before submitting your PR
- 📝 Include docstrings and tests for new functionality

Make Targets
------------

.. code-block:: bash

   make test      # Run full test suite with coverage
   make check     # Run linting, formatting, and typing
   make format    # Auto-format code (black, ruff)
   make clean     # Remove temp files, caches, build artifacts

Testing
-------

Tests are located in the ``tests/`` directory and use `pytest`.

All code contributions must be accompanied by appropriate tests and aim to maintain **100% coverage**:

.. code-block:: bash

   make test

Code Style
----------

This project enforces strict quality and consistency via:

- **Black** – formatting
- **Ruff** – linting and import sorting
- **Mypy** – type checking

.. code-block:: bash

   make check     # Run all style and quality checks
   make format    # Auto-fix lint and formatting issues

Commit & Pull Request Guidelines
--------------------------------

- Use clear, conventional commit messages
- Keep PRs small and focused
- Describe the change and link to any relevant issues
- Pass all CI checks before review

Maintainer
----------

This project is developed and maintained by:

**Roel Kist**  
GitHub: https://github.com/roelkist

License
-------

All contributions are licensed under the MIT License.
