# -*- coding: utf-8 -*-
from flup.server.fcgi import WSGIServer
from sys2do import app


if __name__ == '__main__':
    app.run(host = 'localhost', port = 5000)
#    app.run(host = '192.168.20.41', port = 5000)

#    WSGIServer(app, bindAddress = ("localhost", 8001)).run()
