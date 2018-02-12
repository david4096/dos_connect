# With app.py running start this test
import logging
import sys
import os
import uuid
import requests
import pytest

# setup connection, models and security
from bravado.requests_client import RequestsClient
from bravado.exception import HTTPNotFound
from dos_connect.client.dos_client import Client

SERVER_URL = 'http://localhost:8080/'
http_client = RequestsClient()
# http_client.set_basic_auth('localhost', 'admin', 'secret')
# http_client.set_api_key('localhost', 'XXX-YYY-ZZZ', param_in='header')
local_client = Client(SERVER_URL, http_client=http_client)
client = local_client.client
models = local_client.models

# setup logging
root = logging.getLogger()
root.setLevel(logging.ERROR)
logging.captureWarnings(True)


def test_client_driven_id():
    """ validate server uses client's id """
    Checksum = models.get_model('ga4ghChecksum')
    URL = models.get_model('ga4ghURL')
    CreateDataObjectRequest = models.get_model('ga4ghCreateDataObjectRequest')
    DataObject = models.get_model('ga4ghCreateDataObjectRequest')
    checksum = str(uuid.uuid1())
    id = str(uuid.uuid1())
    # CreateDataObject
    print("..........Create an object............")
    create_data_object = DataObject(
        id=id,
        name="abc",
        size=12345,
        checksums=[Checksum(checksum=checksum, type="md5")],
        urls=[URL(url="a"), URL(url="b")])
    create_request = CreateDataObjectRequest(data_object=create_data_object)
    create_response = client.CreateDataObject(body=create_request).result()
    data_object_id = create_response['data_object_id']
    assert data_object_id == id,  "expected server to use client's id"


def test_duplicate_checksums():
    """ validate expected behavior of multiple creates of same checksum """
    Checksum = models.get_model('ga4ghChecksum')
    URL = models.get_model('ga4ghURL')
    CreateDataObjectRequest = models.get_model('ga4ghCreateDataObjectRequest')
    DataObject = models.get_model('ga4ghCreateDataObjectRequest')
    checksum = str(uuid.uuid1())
    # CreateDataObject
    print("..........Create an object............")
    create_data_object = DataObject(
        name="abc",
        size=12345,
        checksums=[Checksum(checksum=checksum, type="md5")],
        urls=[URL(url="a"), URL(url="b")])
    create_request = CreateDataObjectRequest(data_object=create_data_object)
    create_response = client.CreateDataObject(body=create_request).result()
    data_object_id = create_response['data_object_id']
    print(data_object_id)
    print("..........Create a 2nd  object............")
    create_data_object = DataObject(
        name="xyz",
        size=12345,
        checksums=[Checksum(checksum=checksum, type="md5")],
        urls=[URL(url="c")])
    create_request = CreateDataObjectRequest(data_object=create_data_object)
    create_response = client.CreateDataObject(body=create_request).result()
    data_object_id = create_response['data_object_id']
    print(data_object_id)
    # ListDataObjects
    print("..........List Data Objects...............")
    ListDataObjectsRequest = models.get_model('ga4ghListDataObjectsRequest')
    next_page_token = None
    count = 0
    urls = []
    names = []
    while(True):
        list_request = ListDataObjectsRequest(checksum={'checksum': checksum})
        list_request.page_size = 10
        if next_page_token:
            list_request.next_page_token = next_page_token
        list_response = client.ListDataObjects(body=list_request).result()
        next_page_token = list_response.next_page_token
        for data_object in list_response.data_objects:
            count = count + 1
            urls.extend([url.url for url in data_object.urls])
            names.append(data_object.name)
        if not list_response.next_page_token:
            break
    assert count == 2, 'did not return all objects for {}'.format(checksum)
    for url in ['a', 'b', 'c']:
        assert url in urls, 'expected {} in urls'.format(url)
    for name in ['abc', 'xyz']:
        assert name in names, 'expected {} in names'.format(name)


def test_simple():
    Checksum = models.get_model('ga4ghChecksum')
    URL = models.get_model('ga4ghURL')
    CreateDataObjectRequest = models.get_model('ga4ghCreateDataObjectRequest')
    DataObject = models.get_model('ga4ghCreateDataObjectRequest')
    # CreateDataObject
    print("..........Create an object............")
    create_data_object = DataObject(
        name="abc",
        size=12345,
        checksums=[Checksum(checksum="def", type="md5")],
        urls=[URL(url="a"), URL(url="b")])
    create_request = CreateDataObjectRequest(data_object=create_data_object)
    create_response = client.CreateDataObject(body=create_request).result()
    data_object_id = create_response['data_object_id']
    print(data_object_id)

    # GetDataObject
    print("..........Get the Object we just created..............")
    get_object_response = client.GetDataObject(
        data_object_id=data_object_id).result()
    data_object = get_object_response.data_object
    print(data_object.id)

    # UpdateDataObject
    print("..........Update that object.................")
    UpdateDataObjectRequest = models.get_model('ga4ghUpdateDataObjectRequest')
    update_data_object = DataObject(
        name="abc",
        size=12345,
        checksums=[Checksum(checksum="def", type="md5")],
        urls=[URL(url="a"), URL(url="b"), URL(url="c")])
    update_request = UpdateDataObjectRequest(data_object=update_data_object)
    update_response = client.UpdateDataObject(
        data_object_id=data_object_id, body=update_request).result()
    updated_object = client.GetDataObject(
        data_object_id=update_response['data_object_id']).result().data_object
    print(updated_object.version)
    assert not updated_object.version == data_object.version

    print("..........Create another object w/ same checksum............")
    create_data_object = DataObject(
        name="fubar",
        size=12345,
        checksums=[Checksum(checksum="def", type="md5")],
        urls=[URL(url="foo"), URL(url="bar")])
    create_request = CreateDataObjectRequest(data_object=create_data_object)
    create_response = client.CreateDataObject(body=create_request).result()
    data_object_id = create_response['data_object_id']
    print(data_object_id)

    # ListDataObjects
    print("..........List Data Objects...............")
    ListDataObjectsRequest = models.get_model('ga4ghListDataObjectsRequest')
    next_page_token = None
    count = 0
    while(True):
        list_request = ListDataObjectsRequest(checksum={'checksum': "def"})
        list_request.page_size = 1
        if next_page_token:
            list_request.next_page_token = next_page_token
        list_response = client.ListDataObjects(body=list_request).result()
        next_page_token = list_response.next_page_token
        count = count + 1
        if not list_response.next_page_token:
            break
    assert count > 1


def test_data_objects():
    Checksum = models.get_model('ga4ghChecksum')
    URL = models.get_model('ga4ghURL')
    CreateDataObjectRequest = models.get_model('ga4ghCreateDataObjectRequest')
    DataObject = models.get_model('ga4ghCreateDataObjectRequest')
    # CreateDataObject
    print("..........Create an object............")
    create_data_object = DataObject(
        name="abc",
        size=12345,
        checksums=[Checksum(checksum="def", type="md5")],
        urls=[URL(url="a"), URL(url="b")])
    create_request = CreateDataObjectRequest(data_object=create_data_object)
    create_response = client.CreateDataObject(body=create_request).result()
    data_object_id = create_response['data_object_id']
    print(data_object_id)

    # GetDataObject
    print("..........Get the Object we just created..............")
    get_object_response = client.GetDataObject(
        data_object_id=data_object_id).result()
    data_object = get_object_response.data_object
    print(data_object.id)

    # UpdateDataObject
    print("..........Update that object.................")
    UpdateDataObjectRequest = models.get_model('ga4ghUpdateDataObjectRequest')
    update_data_object = DataObject(
        name="abc",
        size=12345,
        checksums=[Checksum(checksum="def", type="md5")],
        urls=[URL(url="a"), URL(url="b"), URL(url="c")])
    update_request = UpdateDataObjectRequest(data_object=update_data_object)
    update_response = client.UpdateDataObject(
        data_object_id=data_object_id, body=update_request).result()
    updated_object = client.GetDataObject(
        data_object_id=update_response['data_object_id']).result().data_object
    print(updated_object.version)
    assert not updated_object.version == data_object.version

    # Get the old DataObject
    print("..........Get the old Data Object.................")
    old_data_object = client.GetDataObject(
        data_object_id=update_response['data_object_id'],
        version=data_object.version).result().data_object
    print(old_data_object.version)

    # ListDataObjects
    print("..........List Data Objects...............")
    ListDataObjectsRequest = models.get_model('ga4ghListDataObjectsRequest')
    list_request = ListDataObjectsRequest()
    list_response = client.ListDataObjects(body=list_request).result()
    print(len(list_response.data_objects))
    assert len(list_response.data_objects) > 0

    # Get all versions of a DataObject
    print("..........Get all Versions...............")
    versions_response = client.GetDataObjectVersions(
        data_object_id=old_data_object.id).result()
    print(len(versions_response.data_objects))

    # DeleteDataObject
    print("..........Delete the Object...............")
    delete_response = client.DeleteDataObject(
        data_object_id=data_object_id).result()
    print(delete_response.data_object_id)
    try:
        client.GetDataObject(
            data_object_id=update_response['data_object_id']).result()
    except Exception as e:
        print('The object no longer exists, 404 not found. {}'.format(e))

    # Create a Data Object specifying your own version
    print(".......Create a Data Object with our own version..........")
    my_data_object = DataObject(
        name="abc",
        size=12345,
        checksums=[Checksum(checksum="def", type="md5")],
        urls=[URL(url="a"), URL(url="b")],
        version="great-version")
    create_request = CreateDataObjectRequest(data_object=my_data_object)
    create_response = client.CreateDataObject(body=create_request).result()
    data_object_id = create_response['data_object_id']
    data_object = client.GetDataObject(
        data_object_id=data_object_id).result().data_object
    print(data_object.version)

    # Create a Data Object specifying your own ID
    print("..........Create a Data Object with our own ID..............")
    my_data_object = DataObject(
        id="myid",
        file_name="abc",
        checksums=[Checksum(checksum="def", type="md5")],
        urls=[URL(url="a"), URL(url="b")])
    create_request = CreateDataObjectRequest(data_object=my_data_object)
    create_response = client.CreateDataObject(body=create_request).result()
    data_object_id = create_response['data_object_id']
    print(data_object_id)

    # Page through a listing of data objects
    print("..........Page through a listing of Objects..............")
    for i in range(100):
        my_data_object = DataObject(
            name="OBJ{}".format(i),
            aliases=["OBJ{}".format(i)],
            size=10 * i,
            checksums=[Checksum(checksum="def{}".format(i), type="md5")],
            urls=[URL(url="http://{}".format(i))])
        create_request = CreateDataObjectRequest(data_object=my_data_object)
        client.CreateDataObject(body=create_request).result()
    list_request = ListDataObjectsRequest(page_size=10)
    list_response = client.ListDataObjects(body=list_request).result()
    ids = [x.id for x in list_response.data_objects]
    print(list_response.next_page_token)
    print(ids)

    list_request = ListDataObjectsRequest(
        page_size=10, page_token=list_response.next_page_token)
    list_response = client.ListDataObjects(body=list_request).result()
    ids = [x.id for x in list_response.data_objects]
    print(ids)

    # Find a DataObject by alias
    print("..........List Objects by alias..............")
    object_list_request = ListDataObjectsRequest(alias="OBJ1")
    object_list_response = client.ListDataObjects(
        body=object_list_request).result()
    print(object_list_response.data_objects[0].aliases)

    # Find a DataObject by checksum
    print("..........List Objects by checksum..............")
    object_list_request = ListDataObjectsRequest(
        checksum=Checksum(checksum="def1"))
    object_list_response = client.ListDataObjects(
        body=object_list_request).result()
    print(object_list_response.data_objects[0].checksums)

    # Find a DataObject by URL
    print("..........List Objects by url..............")
    object_list_request = ListDataObjectsRequest(url="http://1")
    object_list_response = client.ListDataObjects(
        body=object_list_request).result()
    print(object_list_response.data_objects[0].urls)


def test_data_bundles():
    Checksum = models.get_model('ga4ghChecksum')
    URL = models.get_model('ga4ghURL')
    CreateDataObjectRequest = models.get_model('ga4ghCreateDataObjectRequest')
    DataObject = models.get_model('ga4ghCreateDataObjectRequest')
    ListDataObjectsRequest = models.get_model('ga4ghListDataObjectsRequest')

    print("..........Create some data objects ............")
    for i in range(10):
        my_data_object = DataObject(
            name="OBJ{}".format(i),
            aliases=["OBJ{}".format(i)],
            size=10 * i,
            checksums=[Checksum(checksum="def{}".format(i), type="md5")],
            urls=[URL(url="http://{}".format(i))])
        create_request = CreateDataObjectRequest(data_object=my_data_object)
        client.CreateDataObject(body=create_request).result()
    list_request = ListDataObjectsRequest(page_size=10)
    list_response = client.ListDataObjects(body=list_request).result()
    ids = [x.id for x in list_response.data_objects]
    print(list_response.next_page_token)

    # CreateDataBundle
    print("..........Create a Data Bundle............")
    Checksum = models.get_model('ga4ghChecksum')
    URL = models.get_model('ga4ghURL')
    CreateDataBundleRequest = models.get_model('ga4ghCreateDataBundleRequest')
    DataBundle = models.get_model('ga4ghDataBundle')
    create_data_bundle = DataBundle(
        name="abc",
        size=12345,
        checksums=[Checksum(checksum="def", type="md5")],
        data_object_ids=[x.id for x in list_response.data_objects])
    create_request = CreateDataBundleRequest(data_bundle=create_data_bundle)
    create_response = client.CreateDataBundle(body=create_request).result()
    data_bundle_id = create_response['data_bundle_id']
    print(data_bundle_id)

    # GetDataBundle
    print("..........Get the Bundle we just created..............")
    get_bundle_response = client.GetDataBundle(
        data_bundle_id=data_bundle_id).result()
    data_bundle = get_bundle_response.data_bundle
    print(data_bundle)
    print(data_bundle.id)

    # UpdateDataBundle
    print("..........Update that Bundle.................")
    UpdateDataBundleRequest = models.get_model('ga4ghUpdateDataBundleRequest')
    update_data_bundle = DataBundle(
        name="abc",
        size=12345,
        data_object_ids=[x.id for x in list_response.data_objects],
        checksums=[Checksum(checksum="def", type="md5")],
        aliases=["ghi"])
    update_request = UpdateDataBundleRequest(
        data_bundle_id=data_bundle.id,
        data_bundle=update_data_bundle)
    update_response = client.UpdateDataBundle(
        data_bundle_id=data_bundle_id,
        body=update_request).result()
    print("..........Update that Bundle.................")
    updated_bundle = client.GetDataBundle(
        data_bundle_id=update_response['data_bundle_id']).result().data_bundle
    print('updated_bundle.aliases', updated_bundle.aliases)
    print('updated_bundle.updated', updated_bundle.updated)
    print('data_bundle.aliases', data_bundle.aliases)
    print('data_bundle.updated', data_bundle.updated)
    # print(updated_bundle.version)
    # print(updated_bundle.aliases)
    assert updated_bundle.aliases[0] == 'ghi'

    # ListDataBundles
    print("..........List Data Bundles...............")
    ListDataBundlesRequest = models.get_model('ga4ghListDataBundlesRequest')
    list_request = ListDataBundlesRequest()
    list_response = client.ListDataBundles(body=list_request).result()
    print(len(list_response.data_bundles))

    # Get all versions of a DataBundle
    print("..........Get all Versions of a Bundle...............")
    versions_response = client.GetDataBundleVersions(
        data_bundle_id=data_bundle.id).result()
    print(len(versions_response.data_bundles))

    # Get a DataObject from a bundle
    print("..........Get an Object in a Bundle..............")
    get_bundle_response = client.GetDataBundle(
        data_bundle_id=data_bundle_id).result()
    data_bundle = get_bundle_response.data_bundle
    data_object = client.GetDataObject(
        data_object_id=data_bundle.data_object_ids[0]).result().data_object
    print(data_object.urls)

    # Get all DataObjects from a bundle
    print("..........Get all Objects in a Bundle..............")
    get_bundle_response = client.GetDataBundle(
        data_bundle_id=data_bundle_id).result()
    data_bundle = get_bundle_response.data_bundle
    bundle_objects = []
    for data_object_id in data_bundle.data_object_ids:
        bundle_objects.append(client.GetDataObject(
            data_object_id=data_object_id).result().data_object)
    print([x.name for x in bundle_objects])

    # DeleteDataBundle
    print("..........Delete the Bundle...............")
    delete_response = client.DeleteDataBundle(
        data_bundle_id=data_bundle_id).result()
    print(delete_response.data_bundle_id)
    try:
        client.GetDataBundle(
            data_bundle_id=update_response['data_bundle_id']).result()
    except Exception as e:
        print('The object no longer exists, 404 not found. {}'.format(e))

    # Page through a listing of Data Bundles
    print("..........Page through a listing of Data Bundles..............")
    for i in range(100):
        my_data_bundle = DataBundle(
            name="BDL{}".format(i),
            aliases=["BDL{}".format(i)],
            size=10 * i,
            data_object_ids=data_bundle.data_object_ids,
            checksums=[Checksum(checksum="def", type="md5")],)
        create_request = CreateDataBundleRequest(data_bundle=my_data_bundle)
        client.CreateDataBundle(body=create_request).result()
    list_request = ListDataBundlesRequest(page_size=10)
    list_response = client.ListDataBundles(body=list_request).result()
    ids = [x['id'] for x in list_response.data_bundles]
    print(list_response.next_page_token)
    print(ids)

    list_request = ListDataBundlesRequest(
        page_size=10, page_token=list_response.next_page_token)
    list_response = client.ListDataBundles(body=list_request).result()
    ids = [x['id'] for x in list_response.data_bundles]
    print(ids)

    # Find a DataBundle by alias
    print("..........List Data Bundles by alias..............")
    list_request = ListDataBundlesRequest(
        alias=list_response.data_bundles[0].aliases[0])
    alias_list_response = client.ListDataBundles(body=list_request).result()
    print(list_response.data_bundles[0].aliases[0])
    print(alias_list_response.data_bundles[0].aliases[0])


def test_metrics():
    print("..........OHSU metrics..............")
    r = requests.get(SERVER_URL + 'metrics')
    assert r.status_code == 200, '/metrics should return 200'
    assert 'text/html' in r.headers['content-type'], \
        'content-type should be text/html'
    assert 'dos_connect_data_bundles_count' in r.text, \
        'should return dos_connect_data_bundles_count'
    assert 'dos_connect_data_objects_count' in r.text, \
        'should return dos_connect_data_objects_count'


def test_no_find():
    # this should raise an expected error
    with pytest.raises(HTTPNotFound) as e:
        get_bundle_response = client.GetDataBundle(
            data_bundle_id='NON-EXISTING-KEY').result()
        data_bundle = get_bundle_response.data_bundle
        print(data_bundle)
        print(data_bundle.id)
