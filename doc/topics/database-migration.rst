.. _topics-database-migration:

=========================
Database schema migration
=========================

As mentioned earlier, creating model classes at runtime means that the relevant
database tables will not be created by Django when running syncdb; you will have
to create them yourself. Additionally, if your dynamic models are likely to change
you are going to have to handle database schema (and data) migration.


Schema and data migrations with South
-------------------------------------

Thankfully, `South`_ has a reliable set of functions
to handle schema and database migrations for Django projects.
When used in development, South can suggest migrations but does not attempt to
automatically apply them without interaction from the developer.
This can be different for your system, 
if you are able to recognised the required migration actions with 100% 
confidence, there should be no issue with automatically running schema and data
migrations.
That said, any automatic action is a dangerous one, be sure to err on the side
of caution and avoid destructive operations as much as possible.

.. _South: <http://south.areacode.org/>

Here is a (perfectly safe) way to create a table from your dynamic model.

.. code-block:: python

    from south.db import db

    model_class = generate_my_model_class()
    fields = [(f.name, f) for f in model_class._meta.local_fields]
    table_name = model_class._meta.db_table

    db.create_table(table_name, fields)

    # some fields (eg GeoDjango) require additional SQL to be executed
    db.execute_deferred_sql()

Basic schema migration can also be easily performed. 
Note that if the column type changes in a way that requires data conversion,
you may have to migrate the data manually. 
Remember to run ``execute_deferred_sql`` after adding a new table or column,
to handle a number of special model fields (eg ``ForeignKey``, ``ManyToManyField``, 
GeoDjango fields etc).

.. code-block:: python

    db.add_column(table_name, name, field)
    db.execute_deferred_sql()

    db.rename_column(table_name, old, new) 
    db.rename_table(old_table_name, new_table_name) 

    db.alter_column(table_name, name, field)

Indexes and unique constraints may need to be handled separately:

.. code-block:: python

    db.create_unique(table_name, columns)
    db.delete_unique(table_name, columns)
    db.create_index(table_name, column_names, unique=False)
    db.delete_index(table_name, column_name)

    db.create_primary_key(table_name, columns) # err... does your schema 
    db.delete_primary_key(table_name)          # really need to be so dynamic?


If you really need to delete tables and columns, you can do that too. 
It's a good idea to avoid destructive operations until they're necessary.
Leaving orphaned tables and columns for a period of time and cleaning
them at a later date is perfectly acceptable. You may want to have your
own deletion policy and process, depending on your needs.

.. code-block:: python

    db.delete_table(table_name)
    db.delete_column(table_name, field) 

.. note::
    Note that this South functionality is in the process of being merged into 
    Django core. It will hopefully land in trunk in the near future.

Timing the changes
------------------

Using Django's standard signals, you can perform the relevant actions to
migrate the database schema at the right time.
For example, create the new table on ``post_save`` when ``created=True``.

You may also wish to run some conditional migrations at startup.
For that you'll need to use the ``class_prepared`` signal, but wait until
the models that your factory function require have all been prepared.
The following function handles this timing.
Place it in your ``models.py`` before any of the required models have
been defined and it will call the given function when the time is right:

.. code-block:: python

    when_classes_prepared(app_label, req_models, builder_fn)

The function's implementation can be found in the example code,
in ``surveymaker.utils``.

Another useful feature is to be able to identify when a column rename is
required.
If your dynamic models are defined by Django models, it may be as simple
as determining if an attribute on a model instance has been changed.
You can do this with a combination of ``pre_save`` and ``post_save`` signals
(see ``surveymaker.signals`` in example code for an example of this)
or you can override the `__init__` method of the relevant model to store
the original values when an instance is created. 
The ``post_save`` signal can then detect if a change was made and trigger the
column rename.

If you're concerned about failed migrations causing an inconsistent system
state you may want to ensure that the migrations are in the same transaction
as the changes that cause them.


Introspection
-------------

It may be useful to perform introspection, especially if you leave "deleted"
tables and columns lying around, or if naming conflicts are possible 
(but please try to make them impossible).
This means, the system will react in the way you want it to, 
for example by renaming or deleting the existing tables or by aborting the
proposed schema migration.

Django provides an interface for its supported databases, where existing
table names and descriptions can be easily discovered:

.. code-block:: python

    from django.db.connection import introspection
    from django.db import connection

    name = introspection.table_name_converter(table_name)

    # Is my table already there?
    print name in introspection.table_names()

    description = introspection.get_table_description(connection.cursor(), name)
    db_column_names = [row[0] for row in description]

    # Is my field's column already there?
    print myfield.column in db_column_names

Note that this is limited to standard field types, some fields aren't exactly columns.

