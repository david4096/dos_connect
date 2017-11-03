# Simple server implementation

import connexion
from flask_cors import CORS

import uuid
import datetime
from dateutil.parser import parse
from elasticsearch import Elasticsearch


DEFAULT_PAGE_SIZE = 100

# Our in memory registry
data_objects = {}
data_bundles = {}

_es = Elasticsearch()

# Application logic


def now():
    return str(datetime.datetime.now().isoformat("T") + "Z")


def get_most_recent(key):
    max = {'created': '01-01-1965 00:00:00Z'}
    for version in data_objects[key].keys():
        data_object = data_objects[key][version]
        if parse(data_object['created']) > parse(max['created']):
            max = data_object
    return max


def filter_data_objects(predicate):
    """
    Filters data objects according to a function that acts on each item
    returning either True or False per item.
    """
    return [
        get_most_recent(x[0]) for x in filter(predicate, data_objects.items())]


def add_created_timestamps(doc):
    """
    Adds created and updated timestamps to the document.
    """
    doc['created'] = now()
    doc['updated'] = now()
    return doc


def add_updated_timestamps(doc):
    """
    Adds created and updated timestamps to the document.
    """
    doc['updated'] = now()
    return doc


# Data Object Controllers


def CreateDataObject(**kwargs):
    # TODO Safely create
    body = kwargs['body']['data_object']
    doc = add_created_timestamps(body)
    version = doc.get('version', None)
    if not version:
        doc['version'] = now()
    if doc.get('id', None):
        temp_id = str(uuid.uuid4())
        if data_objects.get(doc['id'], None):
            # issue an identifier if a valid one hasn't been provided
            doc['id'] = temp_id
    else:
        temp_id = str(uuid.uuid4())
        doc['id'] = temp_id
    data_objects[doc['id']] = {}
    data_objects[doc['id']][doc['version']] = doc
    return({"data_object_id": doc['id']}, 200)


def GetDataObject(**kwargs):
    data_object_id = kwargs['data_object_id']
    version = kwargs.get('version', None)
    # Implementation detail, this server uses integer version numbers.
    # Get the Data Object from our dictionary
    data_object_key = data_objects.get(data_object_id, None)
    if data_object_key and not version:
        data_object = get_most_recent(data_object_id)
        return({"data_object": data_object}, 200)
    elif data_object_key and data_objects[data_object_id].get(version, None):
        data_object = data_objects[data_object_id][version]
        return ({"data_object": data_object}, 200)
    else:
        return("No Content", 404)


def GetDataObjectVersions(**kwargs):
    data_object_id = kwargs['data_object_id']
    # Implementation detail, this server uses integer version numbers.
    # Get the Data Object from our dictionary
    data_object_versions_dict = data_objects.get(data_object_id, None)
    data_object_versions = [x[1] for x in data_object_versions_dict.items()]
    if data_object_versions:
        return({"data_objects": data_object_versions}, 200)
    else:
        return("No Content", 404)


def UpdateDataObject(**kwargs):
    data_object_id = kwargs['data_object_id']
    body = kwargs['body']['data_object']
    # Check to make sure we are updating an existing document.
    old_data_object = get_most_recent(data_object_id)
    # Upsert the new body in place of the old document
    doc = add_updated_timestamps(body)
    doc['created'] = old_data_object['created']
    # Set the version number to be the length of the array +1, since
    # we're about to append.
    # We need to safely set the version if they provided one that
    # collides we'll pad it. If they provided a good one, we will
    # accept it. If they don't provide one, we'll give one.
    new_version = doc.get('version', None)
    if new_version and new_version != doc['version']:
        doc['version'] = new_version
    else:
        doc['version'] = now()
    doc['id'] = old_data_object['id']
    data_objects[data_object_id][doc['version']] = doc
    return({"data_object_id": data_object_id}, 200)


def DeleteDataObject(**kwargs):
    data_object_id = kwargs['data_object_id']
    del data_objects[data_object_id]
    return({"data_object_id": data_object_id}, 200)


def ListDataObjects(**kwargs):
    body = kwargs.get('body')


    # "alias": {
    #   "type": "string",
    #   "description": "OPTIONAL\nIf provided will only return Data Objects with the given alias."
    # },
    # "url": {
    #   "type": "string",
    #   "description": "OPTIONAL\nIf provided will return only Data Objects with a that URL matches\nthis string."
    # },
    # "checksum": {
    #   "$ref": "#/definitions/ga4ghChecksumRequest",
    #   "title": "OPTIONAL\nIf provided will only return data object messages with the provided\nchecksum. If the checksum type is provided"
    # },
    clauses = []
    for key in ['alias', 'url', 'checksum']:
        if key in body:
            clauses.append('urls.url:\"{}\"'.format(body[key]))
    q = ' AND '.join(clauses)
    res = _es.search(index='dos', doc_type='dos', q=q)
    print q
    print res
    return({"data_objects": [res['hits']['hits'][0]['_source']]}, 200)


# Data Bundle Controllers


def CreateDataBundle(**kwargs):
    temp_id = str(uuid.uuid4())
    data_bundles[temp_id] = kwargs
    return({"data_bundle_id": temp_id}, 200)


def GetDataBundle(**kwargs):
    data_bundle_id = kwargs['data_bundle_id']
    data_bundle = data_bundles[data_bundle_id]
    return({"data_bundle": data_bundle}, 200)


def UpdateDataBundle(**kwargs):
    # TODO
    # data_bundle_id = kwargs['data_bundle_id']
    # data_bundle = data_bundles[data_bundle_id]
    return(kwargs, 200)


def DeleteDataBundle(**kwargs):
    # TODO
    data_bundle_id = kwargs['data_bundle_id']
    del data_bundles[data_bundle_id]
    return(kwargs, 204)


def ListDataBundles(**kwargs):
    return(kwargs, 200)


def configure_app():
    # The model name has to match what is in
    # tools/prepare_swagger.sh controller.
    app = connexion.App(
        "app",
        specification_dir='.',
        swagger_ui=True,
        swagger_json=True)

    app.add_api('data_objects_service.swagger.json')

    CORS(app.app)
    return app


if __name__ == '__main__':
    app = configure_app()
    app.run(port=8080, debug=True)
