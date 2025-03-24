Usage Guide
===========

This guide covers how to use the `darca-space-manager` module to manage logical local storage spaces and files within them.

SpaceManager
------------

The `SpaceManager` class handles the creation, deletion, listing, and metadata tracking of named "spaces".

**Creating a Space:**

.. code-block:: python

   from darca_space_manager.space_manager import SpaceManager

   manager = SpaceManager()
   manager.create_space("my_space")

**Checking Space Existence:**

.. code-block:: python

   manager.space_exists("my_space")

**Listing and Counting Spaces:**

.. code-block:: python

   manager.list_spaces()
   manager.count_spaces()

**Deleting a Space:**

.. code-block:: python

   manager.delete_space("my_space")

**Getting Metadata:**

.. code-block:: python

   metadata = manager.get_space_metadata("my_space")

SpaceFileManager
----------------

The `SpaceFileManager` class provides file-level access within a managed space, including reading, writing, deleting, and listing files.

**Writing a File:**

.. code-block:: python

   from darca_space_manager.space_file_manager import SpaceFileManager

   file_mgr = SpaceFileManager(manager)
   file_mgr.set_file("my_space", "example.txt", "Hello World")

**Writing YAML or JSON from a Dict:**

.. code-block:: python

   file_mgr.set_file("my_space", "config.yaml", {"debug": True})
   file_mgr.set_file("my_space", "data.json", {"id": 1, "status": "ok"})

**Reading a File:**

Returns raw text, only if the file is ASCII.

.. code-block:: python

   file_content = file_mgr.get_file("my_space", "example.txt")

**Listing Files:**

.. code-block:: python

   file_mgr.list_files("my_space", recursive=True)

**Deleting a File:**

.. code-block:: python

   file_mgr.delete_file("my_space", "example.txt")

**Checking File Existence:**

.. code-block:: python

   file_mgr.file_exists("my_space", "example.txt")
