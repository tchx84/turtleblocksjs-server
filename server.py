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
import json
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
        project_id = get_project_id(handler)
        if project_id and project_id.find('/') >= 0:
            handler.send_response(403, 'forbidden')
            handler.end_headers()
            return None
        if project_id and check_if_missing(method, handler):
            handler.send_response(404, 'not found')
            handler.end_headers()
            return None
        return method(handler, *args, **kwargs)
    return verify


def get_project_id(handler):
    return handler.path.replace('/', '')


def get_project_path(handler):
    project_id = get_project_id(handler)
    return os.path.join(Settings.PROJECTS, project_id)


def get_all_projects():
    filenames = []
    for filename in os.listdir(Settings.PROJECTS):
        filenames.append(filename)
    return json.dumps(filenames)


def get_one_project(handler):
    path = get_project_path(handler)
    with open(path, 'r') as file:
        return file.read()


def check_if_missing(method, handler):
    if method.__name__ == 'do_GET' and \
       not os.path.isfile(get_project_path(handler)):
        return True
    return False


def check_projects_path():
    """Create the project folders if its didn't exists"""
    if not os.path.exists(Settings.PROJECTS):
        os.mkdir(Settings.PROJECTS)


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
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        if get_project_id(self):
            body = get_one_project(self)
        else:
            body = get_all_projects()
        self.wfile.write(body)

    @authorize
    @check
    def do_POST(self):
        self.send_response(200)
        self.end_headers()

        content_len = int(self.headers.getheader('content-length', 0))
        content = self.rfile.read(content_len)

        path = get_project_path(self)
        with open(path, 'w') as file:
            file.write(content)

if __name__ == '__main__':
    check_projects_path()
    httpd = SocketServer.TCPServer((Settings.ADDRESS,
                                    Settings.PORT),
                                   ServerHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

    httpd.server_close()
