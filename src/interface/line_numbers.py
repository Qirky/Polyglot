from __future__ import absolute_import
from .tkimport import Tk

from ..config import *

class LineNumbers(Tk.Canvas):
    def __init__(self, parent, *args, **kwargs):
        Tk.Canvas.__init__(self, parent, *args, **kwargs)
        self.parent     = parent      # buffer
        self.root       = parent.root # interface
        self.textwidget = parent.text # text

    def redraw(self, *args):
        '''Redraws the line numbers at 30 fps'''
        self.delete("all")

        i = self.textwidget.index("@0,0")

        self.config(width=self.textwidget.font.measure(str(max(self.textwidget.get_num_lines(), 10))) + 20)

        w = self.winfo_width() - 5 # Width

        while True:

            dline=self.textwidget.dlineinfo(i)

            if dline is None:
                break

            y = dline[1]
            h = dline[3]

            linenum = int(str(i).split(".")[0])

            # If the linenum is the currently edited linenumber, highlight

            if self.root.local_peer is not None:

                if (self.parent.is_active()) and (linenum == self.root.local_peer.row):

                    x1, y1 = 0, y
                    x2, y2 = w, y + h

                    self.create_rectangle(x1, y1, x2, y2, fill="gray30", outline="gray30")

            self.create_text(w - 4, y, anchor="ne",
                             justify=Tk.RIGHT,
                             text=linenum,
                             font="Font",
                             fill="#d3d3d3")


            i = self.textwidget.index("{}+1line".format(i))

        # Draw a line

        self.create_line(w, 0, w, self.winfo_height(), fill="gray50")#COLOURS["Background"])

        # Draw peer_lables

        if self.textwidget.is_refreshing is False:

            self.textwidget.refresh_peer_labels()