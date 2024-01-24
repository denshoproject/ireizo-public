# ireizo-public - Ireizo API Django App for Names Registry

ireizo-public is a Django app to serve the Ireizo API.

Detailed documentation is in the "docs" directory.

Quick start
-----------

1. Add "ireizo_public" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...,
        "ireizo_public",
    ]

2. Include the irei_public URLconf in your project urls.py like this::

    path("irei/", include("ireizo_public.urls")),

3. Run ``python manage.py migrate`` to create the models.

4. Start the development server and visit the admin.

5. Visit the ``/irei/`` URL to view the API.
