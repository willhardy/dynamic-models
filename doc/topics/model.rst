.. _topics-model:

================================
Defining a dynamic model factory
================================

The basic principle that allows us to create dynamic classes is the built-in
function ``type()``.
Instead of the normal syntax to define a class in Python:

.. code-block:: python

    class Person(object):
        name = "Julia"

The ``type()`` function can be used to create the same class, here is how
the class above looks using the ``type()`` built-in:

.. code-block:: python

    Person = type("Person", (object,), {'name': "Julia"})

Using ``type()`` means you can programatically determine the number and
names of the attributes that make up the class.


Django models
-------------

Django models can be essentially defined in the same manner, with the one
additional requirement that you need to define an attribute called
``__module__``. Here is a simple Django model:

.. code-block:: python

    class Animal(models.Model):
        name = models.CharField(max_length=32)

And here is the equivalent class built using ``type()``:

.. code-block:: python

    attrs = {
        'name': models.CharField(max_length=32), 
        '__module__': 'myapp.models'
    }
    Animal = type("Animal", (models.Model,), attrs)

Any Django model that can be defined in the normal fashion can be
made using ``type()``.


Django's model cache
--------------------

Django automatically caches model classes when you subclass ``models.Model``.
If you are generating a model that has a name that may already exist, you should
firstly remove the existing cached class. 

There is no official, documented way to do this, but current versions of Django
allow you to delete the cache entry directly:

.. code-block:: python

    from django.db.models.loading import cache
    try:
        del cache.app_models[appname][modelname]
    except KeyError:
        pass

.. note::

    When using Django in non-official or undocumented ways, it's highly
    advisable to write unit tests to ensure that the code does what you
    indend it to do. This is especially useful when upgrading Django in
    the future, to ensure that all uses of undocumented features still 
    work with the new version of Django.


Using the model API
-------------------

Because the names of model fields may no longer be known to the developer, 
it makes using Django's model API a little more difficult. 
There are at least three simple approaches to this problem.

Firstly, you can use Python's ``**`` syntax to pass a mapping object as
a set of keyword arguments.
This is not as elegant as the normal syntax, but does the job:

.. code-block:: python

    kwargs = {'name': "Jenny", 'color': "Blue"}
    print People.objects.filter(**kwargs)

A second approach is to subclass ``django.db.models.query.QuerySet`` and provide your own
customisations to keep things clean.
You can attach the customised ``QuerySet`` class by overloading the ``get_query_set`` 
method of your model manager.
Beware however of making things too nonstandard, forcing other developers to
learn your new API.

.. code-block:: python

    from django.db.models.query import QuerySet
    from django.db import models

    class MyQuerySet(QuerySet):
        def filter(self, *args, **kwargs):
            kwargs.update((args[i],args[i+1]) for i in range(0, len(args), 2))
            return super(MyQuerySet, self).filter(**kwargs)

    class MyManager(models.Manager):
        def get_query_set(self):
            return MyQuerySet(self.model)

    # XXX Add the manager to your dynamic model...

    # Warning: This project uses a customised filter method!
    print People.objects.filter(name="Jenny").filter('color', 'blue')

A third approach is to simply provide a helper function that creates either a
preprepared ``kwargs`` mapping or returns a ``django.db.models.Q`` object, which
can be fed directly to a queryset as seen above. This would be like creating a 
new API, but is a little more explicit than subclassing ``QuerySet``.

.. code-block:: python

    from django.db.models import Q

    def my_query(*args, **kwargs):
        """ turns my_query(key, val, key, val, key=val) into a Q object. """
        kwargs.update((args[i],args[i+1]) for i in range(0, len(args), 2))
        return Q(**kwargs)
        
    print People.objects.filter(my_query('color', 'blue', name="Jenny"))


What comes next?
----------------

Although this is enough to define a Django model class, 
if the model isn't in existence when ``syncdb`` is run, 
no respective database tables will be created.
The creation and migration of database tables is covered in
:ref:`database migration <topics-database-migration>`.

Also relevant is the appropriately time regeneration of the model class, 
(`especially` if you want to host using more than one server)
see :ref:`model migration <topics-model-migration>` and, if you would like
to edit the dynamic models in Django's admin, 
:ref:`admin migration <topics-admin-migration>`.


