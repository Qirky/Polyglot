from __future__ import absolute_import
from .tkimport import Tk

class StatusBar(Tk.Frame):
    """ Displays info about """
    def __init__(self, parent, *args, **kwargs):
        Tk.Frame.__init__(self, parent.root, *args, **kwargs)
        self.root = parent # interface

        self.peer_info = {}
        self.labels = []

    def update(self):
        """ Called when the number of peers change """

        # Remove labels
        for label in self.labels:

            label.grid_remove()

        self.peer_info = {}
        
        for n, p_id in enumerate(sorted(self.root.peers.keys())):

            peer = self.root.peers[p_id]

            self.peer_info[p_id] = (peer, Tk.StringVar())

            # Draw

            label = Tk.Label(self, bg=peer.bg, height=1, width=1)
            label.grid(row=0, column = n * 2)
            self.labels.append(label)

            label = Tk.Label(self, textvariable=self.peer_info[p_id][1], bg="Gray", fg="Light Gray", padx=10) # should get this colour from config
            label.grid(row=0, column = (n * 2) + 1)
            self.labels.append(label)

        return

    def redraw(self):
        """ Return """

        # If we have a different peer amount, update the labels

        if len(self.peer_info) != self.root.peers:

            self.update()

        # Count the characters entered by each peer (includes whitespace...)

        counts = {}

        for p_id, peer in self.root.peers.items():

            count = 0

            for i, buf in self.root.buffers.items():

                count += buf.text.peer_tag_doc.count(peer.char)

            counts[p_id] = count

        total = sum([len(buf.text.peer_tag_doc) for buf in self.root.buffers.values()])

        for p_id, count in counts.items():

            percent = ((count / total) * 100) if total > 0 else 0

            # Update string var

            self.peer_info[p_id][1].set("{:.2f}%".format(percent))

        return