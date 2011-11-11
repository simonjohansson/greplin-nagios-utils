#!/usr/bin/env python
# Copyright 2011 The greplin-nagios-utils Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Server that runs Python checks."""

from greplin_nagios_utils import settings
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import memcache
import datetime
import json
import imp
import os
import sys


tornado.options.define(name="debug", default=False, help="run in debug mode", type=bool)
memc = memcache.Client(settings.MEMCACHE)

class CheckHandler(tornado.web.RequestHandler):
    """Handles running a check."""

    def get_json_from_check(self, check):
        try:
            return json.loads(check)
        except:
            return None

    def get_age_from_timestamp(self, timestamp):
        if timestamp:
            try:
                timestamp = float(timestamp)
                data_age = datetime.datetime.fromtimestamp(timestamp)
                now = datetime.datetime.utcnow()
                age = now - data_age
                minutes = age.seconds/60.0 
                minutes += ((age.days*24.0)*60) # Get days in minutes
                return minutes
            except Exception, e:
                print e
        return None

    def get_from_memcached(self, name):
        check = memc.get(name.encode('iso-8859-1'))
        if not check:
            return "UNKNOWN: No check for %s in memcached." % name
        
        check_data = self.get_json_from_check(check)
        if not check_data:
            return "UNKNOWN: Could not load load json from %s.\nWe want jsonified string with the KV-pairs state and timestamp." % name
        
        state = check_data.get('state')
        if not state:
            return "UNKNOWN: Could not extract state from the data for %s.\nRemember to add the state-KV-pair to the jsonified string." % name
        
        timestamp = check_data.get('timestamp')
        if not timestamp:
            return "UNKNOWN: Could not extract a timestamp from the data for %s.\nRemember to add the timestamp-KV-pair to the jsonified string." % name
        
        data_age = self.get_age_from_timestamp(check_data.get('timestamp'))
        if not data_age:
            return "UNKNOWN: Could not extract a timestamp from the data for %s." % name
        
        if data_age > 7:
            return "CRIT: The data is %.2f minutes old.\nLatest data: %s." % (data_age, state)
        if data_age > 4:
            return "WARN: The data is %.2f minutes old.\nLatest data: %s." % (data_age, state)
        return "%s \nData is %.2f minutes old." % (state, data_age)
            
    def get(self, name):
        try:
            sys.stdout = self
            sys.stderr = self
            print self.get_from_memcached(name)
        except SystemExit:
            pass
        
        finally:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__


def main():
    """Starts the web server."""
    tornado.options.parse_command_line()

    application = tornado.web.Application([
        (r"/check/(.+)", CheckHandler),
    ], debug = tornado.options.options.debug)

    httpServer = tornado.httpserver.HTTPServer(application)
    httpServer.listen(settings.CHECKSERVER_MEMCACHE_PORT)

    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
  main()
