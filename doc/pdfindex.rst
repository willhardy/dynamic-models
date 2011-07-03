.. PDF documentation

==================================
Runtime Dynamic Models with Django
==================================

The flexibility of Python and Django allow developers to dynamically create
models to store and access data using Django's ORM. 
But you need to be careful if you go down this road, especially if your models
are set to change at runtime. 
This documentation will cover a number of things to consider when making use 
of runtime dynamic models.

An example implementation of dynamic models is also provided for reference.
It is hosted here on GitHub:
`willhardy/dynamic-models <https://github.com/willhardy/dynamic-models>`_.

This topic was presented at DjangoCon and these notes have been written
as supplementary documentation for that talk.
The talk can be `viewed online here <http://2011.djangocon.eu/talks/22/>`_.


.. include:: /topics/model.rst
.. include:: /topics/model-migration.rst
.. include:: /topics/database-migration.rst
.. include:: /topics/admin-migration.rst
