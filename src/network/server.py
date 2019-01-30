from __future__ import absolute_import

try:
    import socketserver
except ImportError:
    import SocketServer as socketserver

try:
    import queue
except:
    import Queue as queue

import socket
import sys
import time
import os.path
import json

from datetime import datetime
from time import sleep
from getpass import getpass
from hashlib import md5
from threading import Thread

from .network_utils import ThreadedServer, TextHandler
from .message import *

from ..config import *
from ..utils import *
from ..interpreter import DEFAULT_INTERPRETERS

class PolyServer(ThreadedServer):
    """
        This the master Server instance. Other peers on the
        network connect to it and send their keypress information
        to the server, which then sends it on to the others
    """
    bytes  = 2048
    def __init__(self, password="", port=57890, log=False, debug=False):

        # Dict of IDs to OTServer instances

        self.buffers = {i : TextHandler() for i in DEFAULT_INTERPRETERS}
          
        # Address information
        self.hostname = str(socket.gethostname())

        # Listen on any IP
        self.ip_addr  = "0.0.0.0"
        self.port     = int(port)

        # Public ip for server is the first IPv4 address we find, else just show the hostname
        self.ip_pub = self.hostname

        try:

            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self.ip_pub = s.getsockname()[0]
            s.close()

        except OSError:

            pass

        ThreadedServer.__init__(self, (self.ip_addr, self.port), RequestHandler)

        # Reference to the thread that is listening for new connections
        self.server_thread = Thread(target=self.serve_forever)

        self.waiting_for_ack = False # Flagged True after new connected client

        # self.text_constraint = MSG_CONSTRAINT(-1, 0) # default
        
        # Dict of IDs to Client instances
        self.clients = {}

        # ID numbers
        self.max_id  = len(PEER_CHARS) - 1
        self.last_id = -1

        # Set a password for the server
        try:

            self.password = md5(password.encode("utf-8"))

        except KeyboardInterrupt:

            sys.exit("Exited")

        # Set up a char queue
        self.msg_queue = queue.Queue()
        self.msg_queue_thread = Thread(target=self.update_send)

        # Set up log for logging a performance

        if log:
            
            # Check if there is a logs folder, if not create it

            log_folder = os.path.join(ROOT_DIR, "logs")

            if not os.path.exists(log_folder):

                os.mkdir(log_folder)

            # Create filename based on date and times
            
            self.fn = time.strftime("server-log-%d%m%y_%H%M%S.txt", time.localtime())
            path    = os.path.join(log_folder, self.fn)
            
            self.log_file   = open(path, "w")
            self.is_logging = True
            
        else:

            self.is_logging = False
            self.log_file = None

    def get_client_from_addr(self, client_hostname, username):
        """ Returns the server-side representation of a client
            using the client address tuple """
        for client in list(self.clients.values()):
            #if client.hostname == client_hostname and client.name == username:
            if client == (client_hostname, username):
                return client

    def get_client(self, client_id):
        """ Returns the client instance based on the id  """
        return self.clients[client_id]

    def get_client_locs(self):
        return { int(client.id): (int(client.buf_id), int(client.index)) for client in list(self.clients.values()) }

    # def get_text_constraint(self):
    #     return self.text_constraint

    def get_contents(self):
        """ Returns a list with 2 items: dict of buffer index and contents (doc and peer_doc), and
            dict of client index and buf_id/index """
        return [{int(index): buf.get_contents() for index, buf in self.buffers.items()}, self.get_client_locs()]

    def update_all_clients(self):
        """ Sends a reset message with the contents from the server to make sure new user starts the  same  """

        msg = MSG_RESET(-1, *self.get_contents())

        for client in list(self.clients.values()):

            # Tell other clients about the new connection

            if client.connected:

                client.send(msg)
                # client.send(self.get_text_constraint())

        return

    # Operation info
    # ==============

    def handle_operation(self, message):
        """ Handles a new MSG_OPERATION by updating the document, performing operational transformation
            (if necessary) on it and storing it. """

        text = self.buffers[message["buf_id"]]

        new_message = text.receive_message(message)

        if new_message is not None:

            # Get location of peer
            client = self.clients[message["src_id"]]
            client.set_index(message["buf_id"], get_operation_index(message["operation"]))

        return new_message

    def handle_set_mark(self, message):
        """ Handles a new MSG_SET_MARK by updating the client model's index """
        client = self.clients[message["src_id"]]
        client.set_index(message["buf_id"], message["index"])
        return message

    def set_contents(self, data):
        """ Updates the document contents, including the location of user text ranges and marks """
        for key, value in data.items():
            self.contents[key] = value
        return

    def start(self):

        self.running = True
        self.server_thread.start()
        self.msg_queue_thread.start()

        stdout("Server running @ {} on port {}\n".format(self.ip_pub, self.port))

        while True:

            try:

                sleep(0.5)

            except KeyboardInterrupt:

                stdout("\nStopping...\n")

                self.kill()

                break
        return

    def get_next_id(self):
        """ Increases the ID counter and returns it. If it goes over the maximum number allowed, it tries to go to back to the start and 
            checks if that client is connected. If all clients are connected, it returns -1, signalling the client to terminate """
        if self.last_id < self.max_id:
            self.last_id += 1
        else:
            for n in list(range(self.last_id, self.max_id)) + list(range(self.last_id)):
                if n not in self.clients:
                    self.last_id = n
            else:
                return ERR_MAX_LOGINS # error message for max clients exceeded                   
        return self.last_id

    def clear_history(self):
        """ Removes revision history - make sure clients' revision numbers reset """
        for buf in self.buffers.values():
            buf.clear_history()
        self.msg_queue = queue.Queue()
        return

    def wait_for_ack(self, flag):
        """ Sets flag to disregard messages that are not MSG_CONNECT_ACK until all clients have responded """
        if flag == True:
        
            self.waiting_for_ack = True
            self.acknowledged_clients = []

        for client in list(self.clients.values()):

            if client.connected:

                client.send(MSG_REQUEST_ACK(-1, int(flag)))

        return

    def connect_ack(self, message):
        """ Handle response from clients confirming the new connected client """
        
        client_id = message["src_id"]
        
        self.acknowledged_clients.append(client_id)

        # When we have all clients acknowledged, stop waiting
        
        if all([client_id in self.acknowledged_clients for client_id in self.connected_clients()]):

            # Send set_text to all to reset the text

            self.update_all_clients()

            # Stop waiting
        
            self.waiting_for_ack = False
            
            self.acknowledged_clients = []
            
            self.wait_for_ack(False)
        
        return

    def connected_clients(self):
        """ Returns a list of all the connected clients_id's """
        return (client_id for client_id, client in self.clients.items() if client.connected)

    @staticmethod
    def read_configuration_file(filename):
        conf = {}
        with open(filename) as f:
            for line in f.readlines():
                line = line.strip().split("=")
                conf[line[0]] = line[1]
        return conf['host'], int(conf['port'])

    def update_send(self):
        """ This continually sends any operations to clients
        """

        while self.running:

            try:

                msg = self.msg_queue.get_nowait()

                # If logging is set to true, store the message info

                if self.is_logging:

                    self.log_file.write("%.4f" % time.clock() + " " + repr(str(msg)) + "\n")

                # Store the response of the messages
                
                if isinstance(msg, MSG_OPERATION):

                    msg = self.handle_operation(msg)

                elif isinstance(msg, MSG_SET_MARK):

                    msg = self.handle_set_mark(msg)

                # elif isinstance(msg, MSG_CONSTRAINT):

                #     self.text_constraint = msg

                self.respond(msg)

            except queue.Empty:

                sleep(0.01)

        return

    def respond(self, msg):
        """ Update all clients with a message. Only sends back messages to
            a client if the `reply` flag is nonzero. """

        if msg is None:

            return

        for client in list(self.clients.values()):

            if client.connected:

                try:

                    # Send to all other clients and the sender if "reply" flag is true

                    if not self.waiting_for_ack:

                        if (client.id != msg['src_id']) or ('reply' not in msg.data) or (msg['reply'] == 1):

                            client.send(msg)

                except DeadClientError as err:

                    # Remove client if no longer contactable

                    self.remove_client(client.id)

                    print(err)

        return

    def remove_client(self, client_id):

        # Remove from list(s)
            
        if client_id in self.clients:

            self.clients[client_id].disconnect()

        # Notify other clients

        for client in list(self.clients.values()):

            if client.connected:
                   
                client.send(MSG_REMOVE(client_id))

        return
        
    def kill(self):
        """ Properly terminates the server """
        if self.log_file is not None: self.log_file.close()

        outgoing = MSG_KILL(-1, "Warning: Server manually killed by keyboard interrupt. Please close the application")

        for client in list(self.clients.values()):

            if client.connected:

                client.send(outgoing)

                client.force_disconnect()

        sleep(0.5)
        
        self.running = False
        self.shutdown()
        self.server_close()
        
        return

    def write(self, string):
        """ Replaces sys.stdout -- not a good way to do this"""
        if string != "\n":

            outgoing = MSG_RESPONSE(-1, string)

            for client in list(self.clients.values()):

                if client.connected:
                
                  client.send(outgoing)
                    
        return

# Request Handler

class RequestHandler(socketserver.BaseRequestHandler):
    name = None
    client_name = ""

    def client(self):        
        return self.get_client(self.get_client_id())

    def get_client(self, client_id):
        return self.server.get_client(client_id)

    def get_client_id(self):
        return self.client_id

    def authenticate(self, packet):

        addr = self.client_address[0]

        password = packet[0]['password']
        username = packet[0]['name']
        
        if password == self.server.password.hexdigest():

            # See if this is a reconnecting client

            client = self.server.get_client_from_addr(addr, username)

            self.client_info = (addr, username)

            # If the IP address already exists, re-connect the client (if not connected)

            if client is not None:

                if client.connected:

                    # Don't reconnect

                    stdout("User already connected: {}@{}".format(username, addr))

                    self.client_id = ERR_NAME_TAKEN 

                else:

                    # User re-connecting

                    stdout("{} re-connected user from {}".format(username, addr))

                    self.client_id = client.id

            else:

                # Reply with the client id

                stdout("New connected user '{}' from {}".format(username, addr))

                self.client_id = self.server.get_next_id()

        else:

            # Negative ID indicates failed login

            stdout("Failed login from {}".format(addr))

            self.client_id = ERR_LOGIN_FAIL

        # Send back the user_id as a 4 digit number

        reply = "{:04d}".format( self.client_id ).encode()

        self.request.send(reply)

        return self.client_id

    def get_message(self):
        data = self.request.recv(self.server.bytes)
        data = self.reader.feed(data)
        return data

    def handle_client_lost(self, verbose=True):
        """ Terminates cleanly """
        if verbose:
            stdout("Client '{}' @ {} has disconnected".format(self.client_name, self.client_address[0]))
        self.server.remove_client(self.client_id)
        return

    def handle_connect(self, msg):
        """ Stores information about the new client. Wait for acknowledgement from all connected peers before continuing processing messages """
        assert isinstance(msg, MSG_CONNECT)

        # Create the client and connect to other clients

        if self.client_address not in list(self.server.clients.values()):

            new_client = Client(self, name=msg['name'])

            self.client_name = new_client.name
           
            self.connect_clients(new_client) # Contacts other clients

            # Don't accept more messages while connecting

            self.server.wait_for_ack(True)
           
            return new_client

    def leader(self):
        """ Returns the peer client that is "leading" """
        return self.server.leader()
    
    def handle(self):
        """ self.request = socket
            self.server  = ThreadedServer
            self.client_address = (address, port)
        """

        # This takes strings read from the socket and returns json objects

        self.reader = NetworkMessageReader()
        
        # self.messages  = []
        # self.msg_count = 0

        # Password test

        packet = self.get_message()

        if self.authenticate(packet) < 0:

            return

        # Enter loop
        
        while self.server.running:

            try:

                packet = self.get_message()

                # If we get none, just read in again

                if packet is None:

                    self.handle_client_lost()

                    break

            except Exception as e: # TODO be more specific

                # Handle the loss of a client

                self.handle_client_lost()

                break

            for msg in packet:

                if isinstance(msg, MSG_CONNECT):

                    # Add the new client

                    new_client = self.handle_connect(msg)

                    # Clear server history

                    self.server.clear_history()

                elif self.server.waiting_for_ack and isinstance(msg, MSG_CONNECT_ACK):

                    self.server.connect_ack(msg)

                elif not self.server.waiting_for_ack:

                    # Add any other messages to the send queue

                    self.server.msg_queue.put(msg)

        return

    # def store_messages(self, packet):
    #     """ Stores messages to be returned in order with any existing messages in the queue """
    #     self.messages.extend(packet) 
    #     self.messages = list(sorted(self.messages, key=lambda msg: msg["src_id"]))
    #     return

    # def get_message_queue(self):
    #     """ Returns a list of messages that are sorted in ascending 'msg_id' order 
    #         up until we don't find items that are in the next position """
    #     popped = []
    #     i = 0
    #     for msg in self.messages:
    #         if msg["msg_id"] == self.msg_count:
    #             popped.append(msg)
    #             i += 1
    #             self.msg_count += 1
    #         else:
    #             i -= 1
    #             break
    #     self.messages = self.messages[i+1:]
    #     return popped

    def connect_clients(self, new_client):
        """ Update all other connected clients with info on new client & vice versa """

        # Store the client

        self.server.clients[new_client.id] = new_client

        # Connect each client

        msg1 = MSG_CONNECT(new_client.id, new_client.name, new_client.hostname, new_client.port)

        for client in list(self.server.clients.values()):

            # Tell other clients about the new connection

            if client.connected:

                client.send(msg1)

                # Tell the new client about other clients

                if client != self.client_info:

                    msg2 = MSG_CONNECT(client.id, client.name, client.hostname, client.port)

                    new_client.send(msg2)

        return

    def update_client(self):
        """ Send all the previous operations to the client to keep it up to date """

        client = self.client()
        client.send(MSG_SET_ALL(-1, *self.server.get_contents()))
        # client.send(self.server.get_text_constraint())

        return
    
# Keeps information about each connected client

class Client:
    bytes = PolyServer.bytes
    def __init__(self, handler, name=""):

        self.handler = handler

        self.address  = self.handler.client_address
        self.hostname = self.address[0]
        self.port     = self.address[1]

        self.source   = self.handler.request

        # For identification purposes

        self.id   = int(self.handler.get_client_id())
        self.name = name

        # Location

        self.buf_id = 0
        self.index  = 0
        self.connected = True

        # A list of messages to process

        self.messages = []

    def disconnect(self):
        self.connected = False
        self.source.close()

    def connect(self, socket):
        self.connected = True
        self.source = socket
        
    def get_index(self):
        return self.index

    def set_index(self, buf, i):
        """ Sets the buffer id and index for the client """
        self.buf_id = int(buf)
        self.index = int(i)

    def __repr__(self):
        return repr(self.address)

    def send(self, message):
        try:
            self.source.sendall(message.bytes())
        except Exception as e:
            print(e)
            raise DeadClientError(self.hostname)
        return

    def force_disconnect(self):
        return self.handler.handle_client_lost(verbose=False)        

    def __eq__(self, other):
        #return self.address == other
        #return self.hostname == other
        return (self.hostname, self.name) == other

    def __ne__(self, other):
        #return self.address != other
        #return self.hostname != other
        return (self.hostname, self.name) != other

