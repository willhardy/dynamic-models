.. _topics-model-migration:

===============
Model migration
===============

Model migration is simplest when you just regenerate the model using the
usual factory function.
The problem is when the change has been instigated in another process,
the current process will not know that the model class needs to be
regenerated again.
Because it would generally be insane to regenerate the model on every view,
you will need to send a message to other processes, to inform them that
their cached model class is no longer valid.

The most efficient way to check equality is to make a hash describing
the dynamic model,
and let processes compare their hash with the latest version.

Generating a hash
-----------------

You're free to do it however you like, just make sure it is deterministic, 
ie you explicitly order the encoded fields.

In the provided example, a json representation of the fields relevant to 
dynamic model is used to create a hash. For example:

.. code-block:: python

    from django.utils import simplejson
    from django.utils.hashcompat import md5_constructor

    i = my_instance_that_defines_a_dynamic_model
    val = (i.slug, i.name, [i.fields for i in self.field_set.all())
    print md5_constructor(simplejson.dumps(val)).hexdigest()

If you use a dict-like object, make sure you set ``sort_keys=True``
when calling ``json.dumps``.


Synchronising processes
-----------------------

The simplest way to ensure a valid model class is provided to a view is to
validate the hash every time it is accessed.
This means, each time a view would like to use the dynamic model class,
the factory function checks the hash against one stored in a shared data store.
Whenever a model class is generated, the shared store's hash is updated.

Generally you will use something fast for this,
for example memcached or redis.
As long as all processes have access to the same data store, this approach
will work.

Of course, there can be race conditions.
If generating the dynamic model class takes longer in one process then its
hash may overwrite that from a more recent version.

In that case, the only prevention may be to either using the database as a
shared store, keeping all related changes to the one transaction, or by
manually implementing a locking strategy.

Dynamic models are surprisingly stable when the definitions change rarely.
But I cannot vouch for their robustness where migrations are often occuring,
in more than one process or thread.
