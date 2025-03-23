Contributing to darca-yaml
==========================

We're glad you're interested in contributing to **darca-yaml** 🧪📦  
We follow a structured approach that ensures stability, consistency, and quality.

🚫 No forking is necessary — we prefer pull requests directly from branches in this repo.

Getting Started
---------------

1. **Clone this repository**:

   .. code-block:: bash

       git clone https://github.com/roelkist/darca-yaml
       cd darca-yaml

2. **Create a feature branch**:

   .. code-block:: bash

       git checkout -b feature/my-cool-update

3. **Install all dependencies** (including dev + docs):

   .. code-block:: bash

       make install

4. **Write your changes**, ensuring:
   - You follow the existing structure and formatting
   - You include/update tests to maintain 100% test coverage
   - You write/update docstrings and examples

5. **Run all checks before committing**:

   .. code-block:: bash

       make check

   This will run:
   - Code formatters (Black + isort)
   - Pre-commit validations
   - Tests with coverage report
   - Docs build

6. **Commit and push your branch**:

   .. code-block:: bash

       git push origin feature/my-cool-update

7. **Open a Pull Request** to `main`.

   - Add a clear description of what you changed and why
   - Link related issues if applicable
   - CI will automatically validate your PR

Templates
---------

- ✅ Feature Requests: use the GitHub issue template
- 🐞 Bug Reports: include reproduction steps and logs
- 📚 Doc Improvements: feel free to submit directly via PR!

CI/CD Notes
-----------

- `make ci` is used in GitHub Actions to perform the full validation suite
- All individual `make` targets can be run locally for quicker dev cycles

License
-------

By contributing, you agree that your contributions will be licensed under the same license as the project: **MIT**

Thank you 🙌
