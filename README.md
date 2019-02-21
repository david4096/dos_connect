<hr />
<em>- For Demonstration Use Only -</em>

## Data Repository Services Prototype

This demonstration builds on prior work in the Data Object Services schema to explore features
and integrate with Firecloud API services.

Features

* Elasticsearch backend
* Google Cloud Storage Inventory
* Firecloud authorization delegation
* Google Cloud Storage signed URLs

Jump to the swagger UI of the schemas used for this demo here: https://petstore.swagger.io/?url=https://raw.githubusercontent.com/david4096/dos_connect/master/dos_connect/server/data_object_service.swagger.yaml

### Background

dos_connect was originally prepared by Brian Walsh to explore integrating a number of storage
backends with the Data Object Service Schemas. The Data Object Service is an attempt to provide
a cloud neutral, and backend neutral API interface for exchanging metadata about data in
object stores.

### Running the Demonstration

For this demonstration, begin by getting the source for this fork:

```

git clone https://github.com/david4096/dos_connect.git
cd dos_connect

```

Then, create a virtual environment and install dependencies. We will also install jupyter
and the ipykernel for the purposes of interacting with the server.

```
virtualenv env
source env/bin/activate
pip install -r requirements.txt
pip install jupyter ipykernel
ipython kernel install --user --name=drsdemo
```

#### Running Elasticsearch docker

Assuming you have docker installed, you install and run an instance using this command.

```
docker run -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" -e "xpack.security.enabled=false" docker.elastic.co/elasticsearch/elasticsearch:5.5.3
```

This will take a few moments to download and start. When complete these two commands will
initialize the ES index.

```
curl -XPUT "http://localhost:9200/data_objects/_mapping/data_object" -H 'Content-Type: application/json' -d' {"properties": { "checksums": { "properties": { "checksum": { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } }, "type": { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } } } }, "created": { "type": "date" }, "id": { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } }, "name": { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } }, "size": { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } }, "updated": { "type": "date" }, "urls": { "properties": { "url": { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } } } }, "version": { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } } }}'
curl -X PUT localhost:9200/data_objects
```

#### Get your Google Application Credentials

Log in to Google Cloud console and create a service account if you don't already have one. Then,
create, and download the key to your local system in JSON format.

For more information:

https://docs.bmc.com/docs/PATROL4GoogleCloudPlatform/10/creating-a-service-account-key-in-the-google-cloud-platform-project-799095477.html

#### Set environment variables

Before initializing the server, we will set some environment variables to be read at runtime.

```
export GOOGLE_APPLICATION_CREDENTIALS=/location/to/your/creds.json
export BACKEND=dos_connect.server.elasticsearch_backend
export AUTHORIZER=dos_connect.server.firecloud_authorizer
python -m dos_connect.server.app
```

Once the server is started you can view the swagger at http://localhost:8080/ui .

#### Get a firecloud bearer token and start the notebook

Now, to run the demo, we'll get a Firecloud API token. Go to https://api.firecloud.org/ and login
requesting openid scopes by clicking the `Authorize` button in the upper right of the page.

Then, copy the bearer token down and start `jupyter notebook`. The rest of the demo continues
in "Data Services Prototype 2.ipynb".

#### Watch the Video!

https://drive.google.com/open?id=1iyKLh2j3puBczuvqRLj4WakPVL3uHHiO

<hr />



## DOS connect

### concept
Exercise the [GA4GH data-object-schemas]( https://github.com/ga4gh/data-object-schemas)

![image](https://user-images.githubusercontent.com/47808/32701068-36d6db5a-c784-11e7-890d-916109745027.png)


### epics

* As a researcher, in order to maximize the amount of data I can process  from disparate repositories,  I can use DOS to harmonize those repositories
* As a researcher, in order to minimize cloud costs and processing time,  I can use DOS' to harmonized data to make decisions about what platform/region I should use to download from or where my code should execute.
* As a informatician, in order to injest from disparate repositories,  I need to injest an existing repository into DOS
* As a informatician, in order to keep DOS up to date,  I need to observe changes to the repository and automatically update DOS
* As a developer, in order to enable DOS,  I need to integrate DOS into my backend stack


### capabilities

This project provides two high level capabilities:
* observation: long lived services to observe the object store and populate a webserver with [data-object-schema](https://github.com/ga4gh/data-object-schemas/blob/master/proto/data_objects.proto) records. These observations catch add, moves and deletes to the object store.  
* inventory: on demand commands to capture a snapshot of the object store using data-object-schema records.

![image](https://user-images.githubusercontent.com/47808/35762675-ce8720c0-084f-11e8-8b54-40881df595bd.png)



### customizations

The data-object-schema is 'unopinionated' in several areas:
* authentication and authorization is unspecified.
* no specific backend is specified.
* 'system-of-record' for id, if unspecified, is driven by the client.

dos_connect addresses these on the server and client by utilizing `plugin duck-typing`

Server plugins:
* `BACKEND`: for storage. Implementations:  [in-memory](https://github.com/ohsu-comp-bio/dos_connect/blob/master/dos_connect/server/memory_backend.py) and [elasticsearch](https://github.com/ohsu-comp-bio/dos_connect/blob/master/dos_connect/server/elasticsearch_backend.py).  e.g. BACKEND=dos_connect.server.elastic_backend
* `AUTHORIZER`: for AA.
[noop](https://github.com/ohsu-comp-bio/dos_connect/blob/master/dos_connect/server/noop_authorizer.py), [keystone](https://github.com/ohsu-comp-bio/dos_connect/blob/master/dos_connect/server/keystone_api_key_authorizer.py), and [basic](https://github.com/ohsu-comp-bio/dos_connect/blob/master/dos_connect/server/basic_authorizer.py).
 e.g. AUTHORIZER=dos_connect.server.keystone_api_key_authorizer
* `REPLICATOR`: for downstream consumers.
[noop](https://github.com/ohsu-comp-bio/dos_connect/blob/master/dos_connect/server/noop_replicator.py), [keystone](https://github.com/ohsu-comp-bio/dos_connect/blob/master/dos_connect/server/kafka_replicator.py)
 e.g. REPLICATOR=dos_connect.server.kafka_replicator

Client plugins:

All observers and inventory tasks leverage a middleware plugin capability.
* user_metadata(): customize the collection of metadata
* before_store(): modify the data_object before persisting
* md5sum(): calculate the md5 of the file
* id(): customize id
e.g. CUSTOMIZER=dos_connect.apps.aws_customizer

To specify your own customizer, set the `CUSTOMIZER` environmental variable.

For example:
AWS S3 returns a special hash for [multipart files](https://forums.aws.amazon.com/thread.jspa?messageID=456442).  The [aws_customizer](https://github.com/ohsu-comp-bio/dos_connect/blob/master/dos_connect/apps/aws_customizer.py) uses a [lambda](https://github.com/ohsu-comp-bio/dos_connect/tree/master/dos_connect/apps/aws-md5) to calculate the true md5 hash of multipart files.  Other client customizers include [noop](https://github.com/ohsu-comp-bio/dos_connect/blob/master/dos_connect/apps/noop_customizer.py), [url_as_id](https://github.com/ohsu-comp-bio/dos_connect/blob/master/dos_connect/apps/url_as_id_customizer.py), and [smmart](https://github.com/ohsu-comp-bio/dos_connect/blob/master/dos_connect/apps/smmart_customizer.py) (obfuscates paths and associates user metadata)


### setup
see [here](dos_connect/server/README.md)

#### server
Setup: .env file

```
# ******* webserver
# http port
DOS_CONNECT_WEBSERVER_PORT=<port-number>
# configure backend
BACKEND=dos_connect.server.elasticsearch_backend
ELASTIC_URL=<url>
# configure authorizer
AUTHORIZER=dos_connect.server.keystone_api_key_authorizer
# (/v3)
DOS_SERVER_OS_AUTH_URL=<url>
AUTHORIZER_PROJECTS=<project_name>
# replicator
REPLICATOR=dos_connect.server.kafka_replicator
KAFKA_BOOTSTRAP_SERVERS=<url>
KAFKA_DOS_TOPIC=<topic-name>
```

Server Startup:
```
$ alias web='docker-compose -f docker-compose-webserver.yml'
$ web build ; web up -d
```

Client Startup:
**note:** execute `source <openstack-openrc.sh>` first
```
# webserver endpoint
export DOS_SERVER=<url>
# sleep in between inventory runs
export SLEEP=<seconds-to-sleep>
# bucket to monitor
export BUCKET_NAME=<existing-bucket-name>
$ alias client='docker-compose -f docker-compose-swift.yml'
$ client build; client up -d
```

### ohsu implementation:

* see [swagger](https://dms-dev.compbio.ohsu.edu/ga4gh/ui)

* note: you will need to belong to openstack and provide a token from `openstack token issue`

![image](https://user-images.githubusercontent.com/47808/35757585-9e3afd90-0824-11e8-953a-7277104f734c.png)

* see kafak topic 'dos-events' for stream

* the kafka queue is populated with
  ```
  {'method': method, 'doc': doc}
  ```
  where `doc` is a [data_object](https://github.com/ga4gh/data-object-schemas/blob/master/proto/data_objects.proto)  and `method` is one of ['CREATE', 'UPDATE', 'DELETE']


### next steps

* testing
* evangelization
* swagger improvements (403, 401 status codes)
