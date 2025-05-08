Usage
=====

Quick usage examples.

Initialize
----------

.. code-block:: python

    from darca_space_manager.api.space_service import SpaceService

    service = SpaceService()

Create a space
--------------

.. code-block:: python

    service.create_space("myspace", label="Development")

Write a file
------------

.. code-block:: python

    service.write_file("space://myspace/config.yaml", {"env": "dev"})

Read metadata
-------------

.. code-block:: python

    space = service.get_space_info("myspace")
    print("Created at:", space.created_at)
    print("Last modified at:", space.last_modified_at)

Run commands
------------

.. code-block:: python

    result = service.run("space://myspace", ["ls", "-la"])
    print(result.stdout)

Delete space
------------

.. code-block:: python

    service.delete_space("myspace")
