#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from django.db import connection, DatabaseError
from django.db import models
from django.contrib.admin.sites import NotRegistered
from django.db.models.signals import class_prepared
from django.db.models.loading import cache as app_cache

from django.core.urlresolvers import clear_url_caches
from django.utils.importlib import import_module
from django.core.cache import cache
from django.conf import settings

import logging
from south.db import db

logger = logging.getLogger('surveymaker')


def unregister_from_admin(admin_site, model):
    " Removes the dynamic model from the given admin site "

    # First deregister the current definition
    # This is done "manually" because model will be different
    # db_table is used to check for class equivalence.
    for reg_model in admin_site._registry.keys():
        if model._meta.db_table == reg_model._meta.db_table:
            del admin_site._registry[reg_model]

    # Try the normal approach too
    try:
        admin_site.unregister(model)
    except NotRegistered:
        pass

    # Reload the URL conf and clear the URL cache
    # It's important to use the same string as ROOT_URLCONF
    reload(import_module(settings.ROOT_URLCONF))
    clear_url_caches()


def reregister_in_admin(admin_site, model, admin_class=None):
    " (re)registers a dynamic model in the given admin site "

    # We use our own unregister, to ensure that the correct
    # existing model is found 
    # (Django's unregister doesn't expect the model class to change)
    unregister_from_admin(admin_site, model)
    admin_site.register(model, admin_class)

    # Reload the URL conf and clear the URL cache
    # It's important to use the same string as ROOT_URLCONF
    reload(import_module(settings.ROOT_URLCONF))
    clear_url_caches()


def when_classes_prepared(app_name, dependencies, fn):
    """ Runs the given function as soon as the model dependencies are available.
        You can use this to build dyanmic model classes on startup instead of
        runtime. 

        app_name       the name of the relevant app
        dependencies   a list of model names that need to have already been 
                       prepared before the dynamic classes can be built.
        fn             this will be called as soon as the all required models 
                       have been prepared

        NB: The fn will be called as soon as the last required
            model has been prepared. This can happen in the middle of reading
            your models.py file, before potentially referenced functions have
            been loaded. Becaue this function must be called before any 
            relevant model is defined, the only workaround is currently to 
            move the required functions before the dependencies are declared.

        TODO: Allow dependencies from other apps?
    """
    dependencies = [x.lower() for x in dependencies]

    def _class_prepared_handler(sender, **kwargs):
        """ Signal handler for class_prepared. 
            This will be run for every model, looking for the moment when all
            dependent models are prepared for the first time. It will then run
            the given function, only once.
        """
        sender_name = sender._meta.object_name.lower()
        already_prepared = set(app_cache.app_models.get(app_name,{}).keys() + [sender_name])

        if (sender._meta.app_label == app_name and sender_name in dependencies
          and all([x in already_prepared for x in dependencies])):
            db.start_transaction()
            try:
                fn()
            except DatabaseError:
                # If tables are  missing altogether, not much we can do
                # until syncdb/migrate is run. "The code must go on" in this 
                # case, without running our function completely. At least
                # database operations will be rolled back.
                db.rollback_transaction()
            else:
                db.commit_transaction()
                # TODO Now that the function has been run, should/can we 
                # disconnect this signal handler?
    
    # Connect the above handler to the class_prepared signal
    # NB: Although this signal is officially documented, the documentation
    # notes the following:
    #     "Django uses this signal internally; it's not generally used in 
    #      third-party applications."
    class_prepared.connect(_class_prepared_handler, weak=False)


def get_cached_model(app_label, model_name, regenerate=False, get_local_hash=lambda i: i._hash):

    # If this model has already been generated, we'll find it here
    previous_model = models.get_model(app_label, model_name)

    # Before returning our locally cached model, check that it is still current
    if previous_model is not None and not regenerate:
        CACHE_KEY = utils.HASH_CACHE_TEMPLATE % (app_label, model_name)
        if cache.get(CACHE_KEY) != get_local_hash(previous_model):
            logging.debug("Local and shared dynamic model hashes are different: %s (local) %s (shared)" % (get_local_hash(previous_model), cache.get(CACHE_KEY)))
            regenerate = True

    # We can force regeneration by disregarding the previous model
    if regenerate:
        previous_model = None
        # Django keeps a cache of registered models, we need to make room for
        # our new one
        utils.remove_from_model_cache(app_label, model_name)

    return previous_model


def remove_from_model_cache(app_label, model_name):
    """ Removes the given model from the model cache. """
    try:
        del app_cache.app_models[app_label][model_name.lower()]
    except KeyError:
        pass

def create_db_table(model_class):
    """ Takes a Django model class and create a database table, if necessary.
    """
    # XXX Create related tables for ManyToMany etc

    db.start_transaction()
    table_name = model_class._meta.db_table

    # Introspect the database to see if it doesn't already exist
    if (connection.introspection.table_name_converter(table_name) 
                        not in connection.introspection.table_names()):

        fields = _get_fields(model_class)

        db.create_table(table_name, fields)
        # Some fields are added differently, after table creation
        # eg GeoDjango fields
        db.execute_deferred_sql()
        logger.debug("Created table '%s'" % table_name)

    db.commit_transaction()


def delete_db_table(model_class):
    table_name = model_class._meta.db_table
    db.start_transaction()
    db.delete_table(table_name)
    logger.debug("Deleted table '%s'" % table_name)
    db.commit_transaction()


def _get_fields(model_class):
    """ Return a list of fields that require table columns. """
    return [(f.name, f) for f in model_class._meta.local_fields]


def add_necessary_db_columns(model_class):
    """ Creates new table or relevant columns as necessary based on the model_class.
        No columns or data are renamed or removed.
        This is available in case a database exception occurs.
    """
    db.start_transaction()

    # Create table if missing
    create_db_table(model_class)

    # Add field columns if missing
    table_name = model_class._meta.db_table
    fields = _get_fields(model_class)
    db_column_names = [row[0] for row in connection.introspection.get_table_description(connection.cursor(), table_name)]

    for field_name, field in fields:
        if field.column not in db_column_names:
            logger.debug("Adding field '%s' to table '%s'" % (field_name, table_name))
            db.add_column(table_name, field_name, field)


    # Some columns require deferred SQL to be run. This was collected 
    # when running db.add_column().
    db.execute_deferred_sql()

    db.commit_transaction()


def rename_db_column(model_class, old_name, new_name):
    """ Rename a sensor's database column. """
    table_name = model_class._meta.db_table
    db.start_transaction()
    db.rename_column(table_name, old_name, new_name) 
    logger.debug("Renamed column '%s' to '%s' on %s" % (old_name, new_name, table_name))
    db.commit_transaction()


def notify_model_change(model):
    """ Notifies other processes that a dynamic model has changed. 
        This should only ever be called after the required database changes have been made.
    """
    CACHE_KEY = HASH_CACHE_TEMPLATE % (model._meta.app_label, model._meta.object_name) 
    cache.set(CACHE_KEY, model._hash)
    logger.debug("Setting \"%s\" hash to: %s" % (model._meta.verbose_name, model._hash))


HASH_CACHE_TEMPLATE = 'dynamic_model_hash_%s-%s'
