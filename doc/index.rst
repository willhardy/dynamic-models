.. Main landing page for dynamic models documentation.
   TODO: 
        Add an overview, with practical examples
        Discuss reasons to use / not to use this technique
        Add small section on database errors to db migration page.

==================================
Runtime Dynamic Models with Django
==================================

The flexibility of Python and Django allow developers to dynamically create
models to store and access data using Django's ORM. 
But you need to be careful if you go down this road, especially if your models
are set to change at runtime. 
This documentation will cover a number of things to consider when making use 
of runtime dynamic models.

- :ref:`Defining a dynamic model factory <topics-model>`
- :ref:`Model migration <topics-model-migration>`
- :ref:`Database schema migration <topics-database-migration>`
- :ref:`Admin migration <topics-admin-migration>`


Example implementation
======================

An example implementation of dynamic models is also provided for reference.
It is hosted here on GitHub:
`willhardy/dynamic-models <https://github.com/willhardy/dynamic-models>`_.

DjangoCon.eu Talk
=================

This topic was presented at DjangoCon and these notes have been written
as supplementary documentation for that talk.
The talk can be `viewed online here <http://2011.djangocon.eu/talks/22/>`_.


Indices and tables
==================

* :ref:`contents`
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

