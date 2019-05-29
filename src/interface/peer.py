from __future__ import absolute_import
from .tkimport import Tk
    
from ..config import *
from ..utils import *

class Highlight:
    def __init__(self, peer, tag):
        self.peer = peer
        self.tag  = tag
        self.deactivate()

    def __repr__(self):
        return "<Selection: {} - {}>".format(self.start, self.end)

    def __len__(self):
        return (self.end - self.start)
    
    def set(self, start, end):
        """ Set a relative index """
        self.anchor = start # point of origin (could be end or start in terms of length)
        self.start  = min(start, end)
        self.end    = max(start, end)
        self.active = self.start != self.end
    
    def add(self, start, end):
        """ Add a Tk index """
        self.multiple.append((start, end))
        return 
    
    def update(self, old, new):
        if new > self.anchor:
            self.start = self.anchor
            self.end   = new
        elif new < self.anchor:
            self.start = new
            self.end = self.anchor
        else:
            self.hide()
        return

    def shift(self, loc, amount):
        if self.active:
            if loc < self.start:
                self.anchor += amount
                self.start  += amount
                self.end    += amount
            elif loc < self.end:
                self.end += amount
        return

    def is_active(self):
        return self.active
    
    def deactivate(self):
        self.start    = 0
        self.end      = 0
        self.anchor   = 0
        self.active   = False
        self.multiple = []
    
    def show(self):
        """ Adds the highlight tag to the text """
        text = self.peer.get_text_widget()
        if len(self.multiple) > 0:
            for start, end in self.multiple:
                text.tag_add(self.tag, start, end)
        else:
            text.tag_add(self.tag, text.number_index_to_tcl(self.start), text.number_index_to_tcl(self.end))
        self.active = True
        return
    
    def hide(self):
        """ Removes the highlight tag from the text """
        self.clear()
        self.deactivate()
        return

    def remove(self, start, end):
        """ Removes a portion of the highlight """
        if self.active:
            start, end = sorted((start, end))
            size = end - start
            # If the area falls outside of this highlight, do nothing
            if start > self.end or end < self.start:
                return
            elif start < self.start and end < self.end:
                self.end   = self.end + (end - self.start) - size
                self.start = start
            elif start > self.start and end > self.end:
                self.end = start
            elif start > self.start and end < self.end:
                self.end = self.end - size
        return

    def clear(self):
        """ Clears the selection from all text widgets """
        for buf in self.peer.root.buffers.values():
            buf.text.tag_remove(self.tag, "1.0", Tk.END)
        return

class Peer:
    """ Class representing the connected performers within the Tk Widget
    """
    def __init__(self, id_num, name, root, buf=0, row=1, col=0):
        self.id = id_num
        self.char = get_peer_char(self.id)

        self.tk = root.root
        
        self.root   = root # interface
        self.buf_id = buf # Index of the buffer to draw in

        self.name = Tk.StringVar()
        self.name.set(name)

        self.update_colours() # get bg and fg

        self.create_labels()

        self.text_tag = self.get_text_tag(self.id)
        self.code_tag = self.get_code_tag(self.id)
        self.sel_tag  = self.get_select_tag(self.id)
        self.str_tag  = self.get_string_tag(self.id)
        self.mark     = self.get_mark_tag(self.id)
        self.bbox     = None
        self.raised   = False

        # For refreshing the text
        self.hl_eval    = Highlight(self, self.code_tag)
        self.hl_select  = Highlight(self, self.sel_tag)

        self.root.peer_tags.append(self.text_tag)

        # Stat graph

        self.count = 0
        self.graph = None

        self.configure_tags()
        
        # Tracks a peer's selection amount and location
        self.row = row
        self.col = col
        self.index_num = 0
        self.sel_start = "0.0"
        self.sel_end   = "0.0"

        self.visible = True
        self.connected = True

        # self.move(1,0) # create the peer

    def __str__(self):
        return str(self.name.get())

    @staticmethod
    def get_text_tag(p_id):
        return "text_{}".format(p_id)

    @staticmethod
    def get_code_tag(p_id):
        return "code_{}".format(p_id)

    @staticmethod
    def get_select_tag(p_id):
        return "sel_{}".format(p_id)

    @staticmethod
    def get_string_tag(p_id):
        return "str_{}".format(p_id)

    @staticmethod
    def get_mark_tag(p_id):
        return "mark_{}".format(p_id)

    def get_peer_formatting(self, index):

        fg, bg = PeerFormatting(index)

        # if self.root.merge.colour is not None:
            
        #     w = self.root.merge.get_weight()

        #     fg = avg_colour(fg, self.root.merge.colour, w)

        return fg, bg

    def update_colours(self):
        """ Sets the foreground / background colours based on ID """
        self.bg, self.fg = self.get_peer_formatting(self.id)
        return self.bg, self.fg

    def configure_tags(self):
        doing = True
        while doing:
            try:
                for tab in self.root.buffers.values():
                    # Text tags
                    tab.text.tag_config(self.text_tag, foreground=self.bg)
                    tab.text.tag_config(self.str_tag,  foreground=self.fg)
                    tab.text.tag_config(self.code_tag, background=self.bg, foreground=self.fg)
                    tab.text.tag_config(self.sel_tag,  background=self.bg, foreground=self.fg)
                # Label
                self.label.config(bg=self.bg, fg=self.fg)
                self.insert.config(bg=self.bg, fg=self.fg)
                doing = False
            except Tk.TclError:
                pass
        return

    def create_labels(self):
        """ Creates the labels in the current text widget """
        self.label = Tk.Label(self.tk,
                           textvariable=self.name,
                           bg=self.bg,
                           fg=self.fg,
                           font="Font")

        self.insert = Tk.Label(self.tk,
                            bg=self.bg,
                            fg=self.fg,
                            bd=0,
                            height=2,
                            text="", font="Font" )
        return

    def shift(self, amount, *args, **kwargs):
        """ Updates the peer's location relative to its current location by calling `move` """        
        return self.move(self.buf_id, self.index_num + amount, *args, **kwargs)

    def select_shift(self, loc, amount):
        return self.hl_select.shift(loc, amount)

    def select_remove(self, start, end):
        """ Removes an area from the select highlight """
        return self.hl_select.remove(start, end)

    def find_overlapping_peers(self):
        """ Returns True if this peer overlaps another peer's label """

        for peer in self.root.peers.values():

            # If the indices are in overlapping position, on the same row, and the other peer is not already raised

            if (peer != self) and (peer.buf_id == self.buf_id) and peer.visible:

                peer_index = peer.get_index_num()
                this_index = self.get_index_num()

                if (peer_index >= this_index) and (peer_index - this_index < len(str(self))):

                    if not peer.raised and self.is_on_same_row(peer):

                        self.raised = True

                        break

        else:

            self.raised = False

        return self.raised

    def is_on_same_row(self, other):
        """ Returns true if this peer and other peer have the first same value for their tcl index """
        return self.get_row() == other.get_row()
        
    def move(self, buf, loc, raised = False, local_operation = False):
        """ Updates the location of the Peer's label """

        # Get existing buffer id

        old_buffer = self.get_buffer() if (self.get_buf_id() != buf) else None

        # Get new buffer id

        self.buf_id = buf

        # Get the buffer

        if self.visible is False:

            return

        text_widget = self.get_text_widget()

        try:

            document_length = len(text_widget.read())

            # Make sure the location is valid

            if loc < 0:

                self.index_num = 0

            elif loc > document_length:

                self.index_num = document_length

            else:

                self.index_num = loc

            # Work with tcl indexing e.g. "1.0"
            
            index = text_widget.number_index_to_tcl(loc)

            row, col = [int(val) for val in index.split(".")]

            self.row = row
            self.col = col

            index = "{}.{}".format(self.row, self.col)

            # Update the Tk text tag and draw the label

            # print("moving {} to {} / {} ({})".format(str(self), loc, document_length, index))

            text_widget.mark_set(self.mark, index)

            # Redraw all peer labels

            if text_widget.is_refreshing is False:

                text_widget.refresh_peer_labels()

            if old_buffer is not None:

                old_buffer.redraw()

        except Tk.TclError as e:

            print(e)
            
        return self.index_num

    def redraw(self):
        """ Redraws the peer label """

        if self.visible is False:

            return

        buf_widget  = self.get_buffer()
        text_widget = self.get_text_widget()

        # self.bbox = text_widget.bbox(self.mark)

        self.bbox = text_widget.bbox(self.get_tcl_index())

        if self.bbox is not None:

            x, y, width, height = self.bbox

            self.x_val = x - 2

            # Label can go on top of the cursor

            raised = self.find_overlapping_peers()

            if raised:

                self.y_val = (y - height, y - height)

            else:

                self.y_val = (y + height, y)

        else:

            # Move out of view if not needed

            self.x_val = -100
            self.y_val = (-100, -100)

        # Adjust the x/y for the location of the text wiget

        shift_x = text_widget.winfo_x() + buf_widget.winfo_x()
        shift_y = text_widget.winfo_y() + buf_widget.winfo_y()

        self.x_val = self.x_val + shift_x
        self.y_val = tuple(y + shift_y for y in self.y_val)

        self.label.place(x=self.x_val, y=self.y_val[0], anchor="nw")
        self.insert.place(x=self.x_val, y=self.y_val[1], anchor="nw")

        return

    def see(self):
        """ Use text.see to see this peer then redraw -- unused?"""
        self.root.see(self.mark)
        self.redraw()
        return

    def select(self, start, end):
        """ Updates the selected text area for a peer """

        if self.hl_select.active:

            if (start == end == 0) and (self.hl_select.start != 0): # start and end of 0 is a de-select

                self.hl_select.hide()

            else:

                self.hl_select.update(start, end)

        else:

            self.hl_select.set(start, end)

        return

    def select_set(self, start, end):
        """ Override a selection area instead of incrementing """

        if start == end == 0: # start and end of 0 is a de-select

            self.hl_select.hide()

        self.hl_select.set(start, end)

        return

    def select_start(self):
        """ Returns the index of the start of the selection """
        return self.hl_select.start

    def select_end(self):
        """ Returns the index of the end of the selection """
        return self.hl_select.end

    def selection_size(self):
        return len(self.hl_select)

    def select_overlap(self, other):
        """ Returns True if this peer and other have selected areas that overlap """
        a1, b1 = self.select_start(), self.select_end()
        a2, b2 = other.select_start(), other.select_end()
        return (a1 < a2 < b1) or (a1 < b2 < b1)

    def select_contains(self, index):
        """ Returns True if the index is between the start and end of this peer's selection """
        return self.select_start() < index < self.select_end()

    def de_select(self):
        """ Remove (not delete) the selection from the text """
        if self.hl_select.active:
            self.hl_select.hide()
            return True
        else:
            return False

    def remove(self):
        """ Removes the peer from sight, but stays in the address book in case a client reconnects """
        self.connected = False
        self.hl_select.hide()
        self.hide()
        return

    def reconnect(self, name):
        """ Un-hides a peer and updates the name when a client reconnects """
        self.connected = True
        self.visible = True
        self.name.set(name)
        return

    def hide(self):
        """ Moves a label out of view """
        self.x_val = -100
        self.y_val = (-100, -100)
        self.label.place(x=self.x_val, y=self.y_val[0], anchor="nw")
        self.insert.place(x=self.x_val, y=self.y_val[1], anchor="nw")
        self.index_num = -1
        self.visible = False
        return 
    
    def has_selection(self):
        """ Returns True if this peer is selecting any text """
        return self.hl_select.is_active()

    def __highlight_select(self):
        """ Adds background highlighting to text being selected by this peer """
        self.hl_select.clear()
        if self.hl_select.start != self.hl_select.end:
            self.hl_select.show()
        return


    def highlight(self, start_line, end_line):
        """ Highlights (and schedules de-highlight) of block of text. Returns contents
            as a string """

        code = []

        if start_line == end_line: 
            end_line += 1

        for line in range(start_line, end_line):
            
            start = "%d.0" % line
            end   = "%d.end" % line

            # Highlight text only to last character, not whole line

            self.hl_eval.add(start, end)

            code.append(self.get_text_widget().get(start, end))

        self.__highlight_block()
            
        # Unhighlight the line of text

        self.tk.after(200, self.__unhighlight_block)

        return "\n".join(code)

    def __highlight_block(self):
        """ Adds background highlighting for code being evaluated"""
        self.hl_eval.show()
        return

    def __unhighlight_block(self):
        """ Removes highlight formatting from evaluated text """
        self.hl_eval.hide()
        return

    def refresh_highlight(self):
        """ If the text is refreshed while code is being evaluated, re-apply it"""
        if self.hl_eval.active:
            self.__highlight_block()
        if self.hl_select.active:
            self.__highlight_select()
        return

    def refresh(self):
        """ Don't move the marker but redraw it """
        return self.shift(0)

    def get_buf_id(self):
        return self.buf_id

    def get_buffer(self):
        """ Returns the buffer object """
        return self.root.buffers[self.buf_id]

    def get_text_widget(self):
        return self.get_buffer().text

    def in_same_buffer(self, other):
        """ Returns True if the peers are in the same buffer """
        return self.buf_id == other.buf_id

    def get_tcl_index(self):
        """ Returns the index number as a Tkinter index e.g. "1.0" """
        return self.get_text_widget().number_index_to_tcl(self.index_num)

    def get_row(self):
        return int(self.get_tcl_index().split(".")[0])

    def get_col(self):
        return int(self.get_tcl_index().split(".")[1])

    def get_index_num(self):
        """ Returns the index (a single integer) of this peer """
        return self.index_num
    
    def __eq__(self, other):
        return self.id == other.id

    def __ne__(self, other):
        return self.id != other.id
