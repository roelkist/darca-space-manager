darca-space-manager
===================

A lightweight, fully-tested Python library to manage logical file-based spaces.
Ideal for sandboxing, test environments, or dynamic storage orchestration.

|Build Status| |Deploy Status| |CodeCov| |Formatting| |License| |PyPi Version| |Docs|

.. |Build Status| image:: https://github.com/roelkist/darca-space-manager/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/roelkist/darca-space-manager/actions
.. |Deploy Status| image:: https://github.com/roelkist/darca-space-manager/actions/workflows/cd.yml/badge.svg
   :target: https://github.com/roelkist/darca-space-manager/actions
.. |Codecov| image:: https://codecov.io/gh/roelkist/darca-space-manager/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/roelkist/darca-space-manager
   :alt: Codecov
.. |Formatting| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Black code style
.. |License| image:: https://img.shields.io/badge/license-MIT-blue.svg
   :target: https://opensource.org/licenses/MIT
.. |PyPi Version| image:: https://img.shields.io/pypi/v/darca-space-manager
   :target: https://pypi.org/project/darca-space-manager/
   :alt: PyPi
.. |Docs| image:: https://img.shields.io/github/deployments/roelkist/darca-space-manager/github-pages
   :target: https://roelkist.github.io/darca-space-manager/
   :alt: GitHub Pages

🚀 Overview
-----------

**darca-space-manager** provides a simple abstraction over local file storage by organizing content in logical "spaces".
Each space has its own metadata and supports file-level operations such as reading, writing, deleting, and listing — including support for structured content like YAML and JSON.

✨ Features
-----------

- Space creation, deletion, existence checks, and metadata tracking
- File read/write/delete operations within a given space
- Automatic handling of `.yaml`, `.yml`, and `.json` for dictionaries
- Strict ASCII validation when reading text
- Custom exceptions for robust error tracing (`SpaceFileManagerException`, `SpaceManagerException`)
- Parallel-safe test fixtures (100% test coverage)
- CI/CD pipelines, auto-doc generation, and live documentation via GitHub Pages

📦 Installation
---------------

.. code-block:: bash

   pip install darca-space-manager

Or using Poetry:

.. code-block:: bash

   poetry add darca-space-manager

🔧 Usage
--------

.. code-block:: python

   from darca_space_manager import SpaceManager, SpaceFileManager

   sm = SpaceManager()
   sfm = SpaceFileManager()

   sm.create_space("demo")
   sfm.set_file("demo", "example.yaml", {"foo": "bar"})
   print(sfm.get_file("demo", "example.yaml"))  # raw text
   sm.delete_space("demo")

📚 Documentation
----------------

Visit the full documentation:

👉 https://roelkist.github.io/darca-space-manager/

To build locally:

.. code-block:: bash

   make docs

📂 Project Layout
------------------

.. code-block::

   darca_space_manager/
   ├── config.py
   ├── space_executor.py
   ├── space_file_manager.py
   ├── space_manager.py
   └── __version__.py

🧪 Testing
----------

Run all tests using:

.. code-block:: bash

   make test

Coverage and reports:

- Generates `coverage.svg` badge
- Stores HTML output in `htmlcov/`
- Fully parallel test support with `xdist`

🤝 Contributing
---------------

We welcome all contributions!

- Create a new **branch** from `main`
- Use PRs to submit changes
- You can also open feature requests or issues using our GitHub templates

See `CONTRIBUTING.rst` for detailed guidelines.

📄 License
----------

This project is licensed under the MIT License.
See `LICENSE <https://github.com/roelkist/darca-space-manager/blob/main/LICENSE>`_ for details.
