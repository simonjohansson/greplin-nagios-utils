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
import pymongo
import imp
import os
import sys


tornado.options.define(name="debug", default=False, help="run in debug mode", type=bool)


CHECK_CACHE = {}
db = pymongo.Connection(settings.MONGODB).icinga
memc = memcache.Client(settings.MEMCACHE)
server_port = 8111
checkscript_path = '/usr/lib/nagios/plugins/check_%s.py'
special_checks = ['queryd']

class UpdateCheckHandler(tornado.web.RequestHandler):
    """Removes the cached version of a check."""

    def get(self, name): # pylint: disable=W0221
        if name in CHECK_CACHE:
            del CHECK_CACHE[name]



class CheckHandler(tornado.web.RequestHandler):
    """Handles running a check."""

    def get_from_memcached(self, name):
        check = memc.get(name.encode('iso-8859-1'))
        if check:
            print check
        else:
            data = db.services.find_one({'service':name})
            message = data.get('message')
            print "CRIT: The data is old! Last data:\n%s" % message

    def get(self, name):
        """
        The special_check is because sometimes we want to test stuff that might block the server, QUERYD for instance.
        Thants not good because in the end all services that gets tested trough checkserver might turn out UNKNOWN in icinga.
        For this purpose ive added functionality to read data from memcahe and mongodb. Neat.
        If the check has 'substring' in its name and is specified in the special_checks list then they are treated as special
        checks.
        """
        special_check = False
        for check in special_checks:
            if check in name:
                special_check = True    

        if name not in CHECK_CACHE and not special_check:
            filename = checkscript_path % name
            if os.path.exists(filename):
                CHECK_CACHE[name] = imp.load_source('check_%s' % name, filename)
            else:
                raise Exception('No such file: %s' % filename)

        try:
            sys.stdout = self
            sys.stderr = self
            if special_check:
                self.get_from_memcached(name)
            else:
                args = self.get_arguments('arg')
                args.insert(0, 'check_%s' % name)
                CHECK_CACHE[name].check(args)
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
        (r"/update/(.+)", UpdateCheckHandler),
    ], debug = tornado.options.options.debug)

    httpServer = tornado.httpserver.HTTPServer(application)
    httpServer.listen(server_port)

    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
  main()
