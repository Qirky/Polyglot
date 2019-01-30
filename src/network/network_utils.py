from __future__ import absolute_import

try:
    import socketserver
except ImportError:
    import SocketServer as socketserver

from ..utils import *

from ..ot.server import Server, MemoryBackend
from ..ot.text_operation import TextOperation, IncompatibleOperationError as OTError

class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

class TextHandler(Server):
    """ Class for handling Operational Transformation for each buffer """
    def __init__(self):
        # self.document = ""
        # self.backend = MemoryBackend()
        Server.__init__(self, "", MemoryBackend())

        # Document relating to peer chars
        self.peer_tag_doc = ""


    def receive_message(self, message):
        
        # Apply to document
        
        try:
        
            op = self.receive_operation(message["src_id"], message["revision"], TextOperation(message["operation"]))
        
        # debug
        
        except OTError as err:
        
            print(self.document, message["operation"])
        
            raise err

        # Returns None if there are inconsistencies in revision numbers
        # (if last_by_user and last_by_user >= revision)

        if op is None:

            return
        
        message["operation"] = op.ops

        # Apply to peer tags

        peer_op = TextOperation([get_peer_char(message["src_id"]) * len(val) if isinstance(val, str) else val for val in op.ops])
        self.peer_tag_doc = peer_op(self.peer_tag_doc)

        return message

    def get_contents(self):
        # return [self.document, self.get_client_ranges()]
        return (self.document, self.peer_tag_doc)

    def get_client_ranges(self):
        """ Converts the peer_tag_doc into pairs of tuples to be reconstructed by the client """
        if len(self.peer_tag_doc) == 0:
            return []
        else:
            data = []
            p_char = self.peer_tag_doc[0]
            count = 1
            for char in self.peer_tag_doc[1:]:
                if char != p_char:
                    data.append((get_peer_id_from_char(p_char), int(count)))
                    p_char = char
                    count = 1
                else:
                    count += 1
            if count > 0:
                data.append((get_peer_id_from_char(p_char), int(count)))
            return data

    def clear_history(self):
        self.backend = MemoryBackend()