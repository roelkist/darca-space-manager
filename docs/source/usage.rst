Usage Guide
===========

The `darca-space-manager` module provides tools to manage logical storage "spaces" on the local filesystem. These spaces support hierarchical structure, metadata tracking, and file-level access using YAML/JSON-aware operations.

This guide covers both `SpaceManager` and `SpaceFileManager` usage.

.. contents::
   :local:
   :depth: 2

Installation
------------

.. code-block:: bash

   pip install darca-space-manager

Spaces Overview
---------------

A "space" is a directory with a metadata file (`metadata.yaml`) that is automatically indexed and managed.

You can create nested spaces such as `project/2025/reports`, track them with labels, and safely manipulate files within them.

SpaceManager
------------

The `SpaceManager` handles:

- Creating and deleting spaces (flat or nested)
- Listing spaces with optional label filtering
- Accessing space metadata
- Creating/removing subdirectories inside a space

.. code-block:: python

   from darca_space_manager.space_manager import SpaceManager

   manager = SpaceManager()

**Creating a Space:**

.. code-block:: python

   # Create a root-level space
   manager.create_space("projects")

   # Create a nested space inside an existing one
   manager.create_space("reports", label="pdf", parent_path="projects/2025")

**Checking Space Existence:**

.. code-block:: python

   exists = manager.space_exists("reports")

**Listing Spaces:**

.. code-block:: python

   all_spaces = manager.list_spaces()

   # Filter by label
   pdf_spaces = manager.list_spaces(label_filter="pdf")

**Accessing Metadata:**

.. code-block:: python

   metadata = manager.get_space("reports")
   print(metadata["created_at"], metadata["path"])

**Creating a Directory Inside a Space:**

.. code-block:: python

   manager.create_directory("projects", "2025/data/charts")

**Removing a Directory:**

.. code-block:: python

   manager.remove_directory("projects", "2025/data/charts")

**Deleting a Space:**

.. code-block:: python

   manager.delete_space("reports")

**Space Index Refresh:**

Spaces are auto-indexed on init and after any mutation, but you can trigger it manually:

.. code-block:: python

   manager.refresh_index()

SpaceFileManager
----------------

The `SpaceFileManager` allows file-level operations inside a named space, with support for structured data formats.

.. code-block:: python

   from darca_space_manager.space_file_manager import SpaceFileManager

   file_mgr = SpaceFileManager()

**Writing Files (Text):**

.. code-block:: python

   file_mgr.set_file("reports", "summary.txt", "Quarterly Report Summary")

**Writing Files (YAML / JSON):**

.. code-block:: python

   # YAML from dict
   file_mgr.set_file("reports", "config.yaml", {"version": 1, "enabled": True})

   # JSON from dict
   file_mgr.set_file("reports", "data.json", {"items": [1, 2, 3]})

**Reading Files:**

.. code-block:: python

   # Read raw text
   txt = file_mgr.get_file("reports", "summary.txt")

   # Read structured YAML/JSON into dict
   config = file_mgr.get_file("reports", "config.yaml", load=True)

**Listing Files:**

.. code-block:: python

   files = file_mgr.list_files("reports")
   nested_files = file_mgr.list_files("reports", recursive=True)

**Checking File Existence:**

.. code-block:: python

   if file_mgr.file_exists("reports", "summary.txt"):
       print("Exists!")

**Deleting Files:**

.. code-block:: python

   file_mgr.delete_file("reports", "summary.txt")

Error Handling
--------------

Both `SpaceManager` and `SpaceFileManager` raise consistent exceptions:

- `SpaceManagerException`
- `SpaceFileManagerException`

These exceptions include error codes and contextual metadata:

.. code-block:: python

   from darca_space_manager.space_manager import SpaceManagerException

   try:
       manager.get_space("nonexistent")
   except SpaceManagerException as e:
       print(e.message, e.error_code, e.metadata)

Environment Configuration
-------------------------

By default, data is stored under:

.. code-block:: text

   ~/.local/share/darca_space/

You can override this using the `DARCA_SPACE_BASE` environment variable:

.. code-block:: bash

   export DARCA_SPACE_BASE=/custom/path/to/storage

Directory Layout
----------------

A typical layout under the hood looks like this:

.. code-block:: text

   ~/.local/share/darca_space/
   ├── metadata/
   │   └── spaces_index.yaml
   ├── logs/
   └── spaces/
       ├── projects/
       │   ├── metadata.yaml
       │   └── 2025/
       │       └── reports/
       │           ├── config.yaml
       │           └── summary.txt

Final Notes
-----------

- All paths and files are validated to remain within their space boundaries
- YAML and JSON files are safely parsed and saved
- Metadata is automatically refreshed and indexed
- Exceptions include structured context for better debugging

