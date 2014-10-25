#!/usr/bin/env python

# Copyright (c) 2014 Martin Abente Lahaye. - tch@sugarlabs.org
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

import os
import logging
import SimpleHTTPServer
import SocketServer

from settings import Settings


def authorize(method):
    """ just a basic method for authorization """
    def verify(handler, *args, **kwargs):
        if not 'x-api-key' in handler.headers or \
               handler.headers['x-api-key'] != Settings.API_KEY:
            handler.send_response(401, "unauthorized")
            handler.end_headers()
            return None
        return method(handler, *args, **kwargs)
    return verify


def check(method):
    """ put things under control """
    def verify(handler, *args, **kwargs):
        if not 'x-project-id' in handler.headers or \
               not isinstance(handler.headers['x-project-id'], str) or \
               not handler.headers['x-project-id'].find('/') < 0 or \
               not os.path.exists(get_project_path(handler)):
            handler.send_response(404, "not found")
            handler.end_headers()
            return None
        return method(handler, *args, **kwargs)
    return verify


def get_project_path(handler):
    return os.path.join(Settings.PROJECTS, handler.headers['x-project-id'])


class ServerHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_OPTIONS(self):
        logging.info(self.headers)

        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods',
                         'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers',
                         'x-project-id, x-api-key')

    @authorize
    @check
    def do_GET(self):
        logging.info(self.headers)

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        path = get_project_path(self)
        with open(path, 'r') as file:
            self.wfile.write(file.read())

    @authorize
    @check
    def do_POST(self):
        logging.info(self.headers)

        self.send_response(200)
        self.end_headers()

        content_len = int(self.headers.getheader('content-length', 0))
        content = self.rfile.read(content_len)
        logging.error(content)

        path = get_project_path(self)
        with open(path, 'w') as file:
            file.write(content)

httpd = SocketServer.TCPServer((Settings.ADDRESS,
                               Settings.PORT),
                               ServerHandler)
httpd.serve_forever()
