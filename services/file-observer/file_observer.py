#!/usr/bin/env python
import os
import sys
from string import Template
from watchdog.events import PatternMatchingEventHandler, FileCreatedEvent
from watchdog.events import DirCreatedEvent
from watchdog.observers.polling import PollingObserver
import datetime
import urlparse
import urllib
import socket
import logging
import time
import argparse
from stat import *
import json
import re
from file_observer_customizations import md5sum, user_metadata
from customizations import store, custom_args


class DOSHandler(PatternMatchingEventHandler):

    """Creates DOS object in store in response to matched events."""

    def __init__(self, args):
        super(DOSHandler, self).__init__(args.patterns,
                                         args.ignore_patterns,
                                         args.ignore_directories,
                                         args.case_sensitive)
        self.monitor_directory = args.monitor_directory
        self.dry_run = args.dry_run

    def on_any_event(self, event):
        try:
            self.process(event)
        except Exception as e:
            logger.exception(e)

    def process(self, event):
        if (event.is_directory):
            return

        event_methods = {
            'deleted': 'ObjectRemoved:Delete',
            'moved': 'ObjectCreated:Copy',
            'created': 'ObjectCreated:Put',
            'modified': 'ObjectModified'
        }
        _id = re.sub(r'^' + self.monitor_directory + '/', '', event.src_path)
        _url = self.path2url(event.src_path)
        event.src_path.lstrip(self.monitor_directory)
        data_object = {
          "id": _id,
          "urls": [{
              'url': _url,
              "system_metadata": {"event_type":
                                  event_methods.get(event.event_type),
                                  "bucket_name": self.monitor_directory}}]

        }

        if not event.event_type == 'deleted':
            f = os.stat(event.src_path)
            if not S_ISREG(f.st_mode):
                return
            ctime = datetime.datetime.fromtimestamp(f.st_ctime).isoformat()
            mtime = datetime.datetime.fromtimestamp(f.st_mtime).isoformat()
            data_object = {
              "id": _id,
              "size": f.st_size,
              # The time, in ISO-8601,when S3 finished processing the request,
              "created":  ctime,
              "updated":  mtime,
              "checksums": [{"checksum": md5sum(event.src_path, _url),
                             'type': 'md5'}],
              "urls": [{
                  'url': _url,
                  "user_metadata": user_metadata(event.src_path),
                  "system_metadata": {"event_type":
                                      event_methods.get(event.event_type),
                                      "bucket_name": self.monitor_directory}}]
            }
        store(args, data_object)

    def path2url(self, path):
        return urlparse.urljoin(
          'file://{}'.format(socket.gethostname()),
          urllib.pathname2url(os.path.abspath(path)))


if __name__ == "__main__":
    # logging.basicConfig(level=logging.INFO,
    #                     format='%(asctime)s - %(message)s',
    #                     datefmt='%Y-%m-%d %H:%M:%S')

    argparser = argparse.ArgumentParser(
        description='Consume events from directory, populate store')

    argparser.add_argument('--patterns', '-p',
                           help='''patterns to trigger events''',
                           default=None)

    argparser.add_argument('--ignore_patterns', '-ip',
                           help='''patterns to ignore''',
                           default=None)

    argparser.add_argument('--ignore_directories', '-id',
                           help='''dir events''',
                           default=False)

    argparser.add_argument('--case_sensitive', '-cs',
                           help='''case_sensitive''',
                           default=False)

    argparser.add_argument('--inventory', '-i',
                           help='''create event for existing files''',
                           default=False,
                           action='store_true')

    argparser.add_argument('--dry_run', '-d',
                           help='''dry run''',
                           default=False,
                           action='store_true')

    argparser.add_argument('--polling_interval', '-pi',
                           help='interval in seconds between polling '
                                'the file system',
                           default=60)

    argparser.add_argument("-v", "--verbose", help="increase output verbosity",
                           default=False,
                           action="store_true")

    argparser.add_argument('monitor_directory',
                           help='''directory to monitor''',
                           default='.')

    custom_args(argparser)

    args = argparser.parse_args()

    if args.verbose:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    else:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    logger = logging.getLogger(__name__)

    logger.debug(args)
    path = args.monitor_directory
    event_handler = DOSHandler(args)

    if args.inventory:
        logger.debug("inventory {}".format(path))
        for root, dirs, files in os.walk(path):
            if not args.ignore_directories:
                for name in dirs:
                    event_handler.on_any_event(DirCreatedEvent(
                        os.path.join(root, name)))
            for name in files:
                if args.ignore_patterns and re.search(args.ignore_patterns,
                                                      os.path.join(root, name)
                                                      ):
                    continue
                if args.patterns and not re.search(args.patterns,
                                                   os.path.join(root, name)):
                    continue
                event_handler.on_any_event(FileCreatedEvent(
                        os.path.join(root, name)))
    else:
        logger.debug("observing {}".format(path))
        observer = PollingObserver(args.polling_interval)
        observer.schedule(event_handler, path, recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
