Concepts
========

Spaces
------

A logical storage unit with metadata:

- name
- path
- label
- parent
- created_at
- last_modified_at

Space URIs
----------

Standardized addressing of space paths::

    space://<space_name>/<optional_sub_path>

Example::

    space://myspace/config.yaml

Used for file management and command execution context.

Metadata
--------

- **created_at**: Immutable space creation timestamp
- **last_modified_at**: Updated when space metadata changes or file operations occur.

Concurrency
-----------

- All operations on spaces are guarded by `SpaceOperationLock` to prevent race conditions.

Path Enforcement
----------------

- All file operations use `SpacePathManager` to guarantee space boundary isolation.
