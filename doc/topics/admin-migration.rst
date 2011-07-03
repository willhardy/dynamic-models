.. _topics-admin-migration:

===============
Admin migration
===============

When using Django's admin, you will need to update the admin site
when your dynamic model changes.
This is one area where it is not entirely straightforward,
because we are now dealing with a "third-party app" that does not
expect the given models to change.
That said, there are ways around almost all of the main problems.

Unregistering
-------------

Calling ``site.unregister`` will not suffice,
the model will have changed and the admin will not find the old dynamic model
when given the new one.
The solution is however straightforward,
we search manually using the name of the old dynamic model,
which will often be the same as the new model's name.

The following code ensures the model is unregistered:

.. code-block:: python

    from django.contrib import admin 
    site = admin.site
    model = my_dynamic_model_factory()

    for reg_model in site._registry.keys():
        if model._meta.db_table == reg_model._meta.db_table:
            del site._registry[reg_model]

    # Try the regular approach too, but this may be overdoing it
    try:
        site.unregister(model)
    except NotRegistered:
        pass

.. note::

    Again, this is accessing undocumented parts of Django's core.
    Please write a unit test to confirm that it works,
    so that you will notice any backwards incompatible changes in a 
    future Django update.


Clearing the URL cache
----------------------

Even though you may have successfully re-registered a newly changed model,
Django caches URLs as soon as they are first loaded. 
The following idiomatic code will reset the URL cache,
allowing new URLs to take effect.

.. code-block:: python

    from django.conf import settings
    from django.utils.importlib import import_module
    from django.core.urlresolvers import clear_url_caches

    reload(import_module(settings.ROOT_URLCONF))
    clear_url_caches()


Timing Admin updates
--------------------

Once again, Django's signals can be used to trigger an update of the Admin.
Unfortunately, this cannot be done when the change takes place in another
process.

Because Django's admin doesn't use your factory function to access the model
class (it uses the cached version), it cannot check the hash for validity
nor can it rebuild when necessary.

This isn't a problem if your Admin site is carefully place on a single server
and all meaningful changes take place on the same instance.
In reality, it's not always on a single server and background processes
and tasks need to be able to alter the schema.

A fix may involve pushing the update to the admin process,
be it a rudimentary hook URL, or something much more sophisticated.

