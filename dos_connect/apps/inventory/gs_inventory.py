from google.cloud import storage

import json
import uuid
import argparse
import logging
import urllib
import time
import pprint
import sys
from datetime import datetime
from .. import common_args, common_logging,  store, custom_args


def to_dos(bucket, record):
    system_metadata = {}
    for field in ["crc32c", "etag", "storageClass", "bucket", "generation"
                  "metageneration", "contentType"]:
        if field in record:
            system_metadata[field] = record[field]
    system_metadata['location'] = bucket.location
    system_metadata['event_type'] = 'ObjectCreated:Put'

    user_metadata = record.get('metadata', None)

    _id = record['id']
    _urls = [{
            'url': record['mediaLink'],
            "system_metadata": system_metadata,
            "user_metadata": user_metadata
        }]

    _urls.append({'url': 'gs://{}/{}'.format(record['bucket'], record['name'])})
    print(record)
    # {u'kind': u'storage#object', u'contentType': u'application/octet-stream',
    #  u'name': u'blobs/04afef80d6c43a4fb4ced4964759e20a469c5635e722ba4444d543777be93517.56a482ce60a88d7f7473b82413a43d9841407f5c.7baf596dea26f9a786b92fb4fe3c94a5-2.5b6099e8',
    #  u'timeCreated': u'2019-01-30T19:17:02.831Z', u'generation': u'1548875822831834', u'componentCount': 1,
    #  u'bucket': u'org-humancellatlas-dss-checkout-dev', u'updated': u'2019-01-30T19:17:02.831Z', u'crc32c': u'W2CZ6A==',
    #  u'metageneration': u'1',
    #  u'mediaLink': u'https://www.googleapis.com/download/storage/v1/b/org-humancellatlas-dss-checkout-dev/o/blobs%2F04afef80d6c43a4fb4ced4964759e20a469c5635e722ba4444d543777be93517.56a482ce60a88d7f7473b82413a43d9841407f5c.7baf596dea26f9a786b92fb4fe3c94a5-2.5b6099e8?generation=1548875822831834&alt=media',
    #  u'storageClass': u'MULTI_REGIONAL', u'timeStorageClassUpdated': u'2019-01-30T19:17:02.831Z',
    #  u'etag': u'CNqx4omcluACEAE=',
    #  u'id': u'org-humancellatlas-dss-checkout-dev/blobs/04afef80d6c43a4fb4ced4964759e20a469c5635e722ba4444d543777be93517.56a482ce60a88d7f7473b82413a43d9841407f5c.7baf596dea26f9a786b92fb4fe3c94a5-2.5b6099e8/1548875822831834',
    #  u'selfLink': u'https://www.googleapis.com/storage/v1/b/org-humancellatlas-dss-checkout-dev/o/blobs%2F04afef80d6c43a4fb4ced4964759e20a469c5635e722ba4444d543777be93517.56a482ce60a88d7f7473b82413a43d9841407f5c.7baf596dea26f9a786b92fb4fe3c94a5-2.5b6099e8',
    #  u'size': u'67108865'}
    checksums = ['etag', 'md5Hash', 'crc32c']
    checksum_records = []
    for checksum in checksums:
        if checksum in record:
            checksum_records.append({"checksum": record[checksum], "type": checksum})

    return {
      "id": str(uuid.uuid4()),
      "size": record['size'],
      "created": record['timeCreated'],  # datetime.strptime(record['timeCreated'], "%Y-%m-%dT%H:%M:%S.%fZ"),
      "updated": record['updated'],  # datetime.strptime(record['updated'], "%Y-%m-%dT%H:%M:%S.%fZ"),
      "checksums": checksum_records,
      "urls": _urls
    }


def process(args, bucket, record):
    if not record['kind'] == "storage#object":
        return True

    store(args, to_dos(bucket, record))
    return True


def populate_args(argparser):
    """add arguments we expect """
    argparser.add_argument('bucket_name',
                           help='''bucket_name to inventory''',
                           )
    common_args(argparser)
    custom_args(argparser)


if __name__ == '__main__':  # pragma: no cover
    argparser = argparse.ArgumentParser(
        description='Consume blob info from gs, populate webserver')
    populate_args(argparser)

    args = argparser.parse_args()

    common_logging(args)

    logger = logging.getLogger(__name__)
    logger.debug(args)

    # Instantiates a client
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(args.bucket_name)
    blobs = bucket.list_blobs()
    for blob in blobs:
        process(args, bucket, blob.__dict__['_properties'])
