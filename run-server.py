#!/usr/bin/env python

"""
    Polyglot-Server
    ------------

    The Polyglot Server runs on the local machine by default on port 57890.
    This needs to be running before connecting using the client application.
    See "run-client.py" for more information on how to connect to the
    server. 

"""
from src.network import PolyServer
from getpass import getpass

try:

    myServer = PolyServer(password=getpass("Password (leave blank for no password): "))
    myServer.start()

# Exit cleanly on Ctrl + c

except KeyboardInterrupt:

    pass