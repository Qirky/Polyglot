from __future__ import absolute_import
from .tkimport import Tk, tkFileDialog, tkMessageBox, tkFont

from .textbox import ThreadSafeText
from .console import Console
from .line_numbers import LineNumbers
from .drag import Dragbar
from .mouse import Mouse

from ..config import *
from ..utils import *
from ..network.message import *
from ..interpreter import DEFAULT_INTERPRETERS

import string

class BufferTab(Tk.LabelFrame):
    """ Widget for containing a Text buffer, console, and scroll widgets for each
        language used in Polyglot """
    def __init__(self, parent, buffer_id, lang, sync_to_espgrid, *args, **kwargs):
        
        Tk.LabelFrame.__init__(self, parent.buffer_frame, 
            text=str(DEFAULT_INTERPRETERS[buffer_id].name), 
            padx=0, pady=0, 
            bg=COLOURS["Background"],
            fg="White", 
            font="Font"
        )

        # self.grid_propagate(False)

        self.root = parent # interface
        self.lang = lang
        self.sync_to_espgrid = sync_to_espgrid
        self.id   = int(buffer_id)

        # Used to adjust refresh rate

        self.frame_count = self.frame_reset = 2

        # Text box
        self.text=ThreadSafeText(self, bg=COLOURS["Background"], 
                                       insertbackground=COLOURS["Background"],
                                       fg="white",
                                       bd=0, 
                                       highlightthickness=0)

        self.text.grid(row=0, column=1, sticky=Tk.NSEW)

        # Line numbers
        self.line_numbers = LineNumbers(self, width=5, bg=COLOURS["Background"], bd=0, highlightthickness=0)
        self.line_numbers.grid(row=0, column=0, sticky=Tk.NSEW)

        # Scroll bar
        self.scroll = Tk.Scrollbar(self)
        self.scroll.grid(row=0, column=2, sticky=Tk.NSEW)
        self.scroll.config(command=self.text.yview)
        self.text.config(yscrollcommand=self.scroll.set)

        # Drag is a small line that changes the size of the console
        self.drag = Dragbar(self, bg="white", height=2  )
        self.drag.grid(row=1, column=0, stick=Tk.NSEW, columnspan=3)

        # Console Box

        self.console = Console(self, 
            bg=COLOURS["Console"], 
            fg="white", 
            height=5, 
            font="Font", 
            highlightthickness=0
        )
        
        self.console.grid(row=2, column=0, columnspan=2, stick=Tk.NSEW)

        self.console.scroll = Tk.Scrollbar(self)
        self.console.scroll.grid(row=2, column=2, sticky=Tk.NSEW)
        self.console.scroll.config(command=self.console.yview)
        self.console.config(yscrollcommand=self.console.scroll.set)

        # Weighting on window resize

        self.rowconfigure(0, weight=3) # Textbox
        self.rowconfigure(1, weight=0) # Dragbar
        self.rowconfigure(2, weight=1) # Console

        self.columnconfigure(0, weight=0) # Line numbers
        self.columnconfigure(1, weight=1) # Text and console

        # Key bindings

        CtrlKey = "Command" if SYSTEM == MAC_OS else "Control"

        # Disable by default

        disable = lambda e: "break"

        for key in list(string.digits + string.ascii_letters) + ["slash"]:

            self.text.bind("<{}-{}>".format(CtrlKey, key), disable)

        self.text.bind("escape", disable)

        # Evaluating code

        self.text.bind("<Key>", self.key_press)

        self.text.bind("<{}-Return>".format(CtrlKey), self.evaluate)
        self.text.bind("<Alt-Return>", self.single_line_evaluate)

        self.text.bind("<{}-Right>".format(CtrlKey),    self.key_ctrl_right)
        self.text.bind("<{}-Left>".format(CtrlKey),     self.key_ctrl_left)
        self.text.bind("<{}-Home>".format(CtrlKey),     self.key_ctrl_home)
        self.text.bind("<{}-End>".format(CtrlKey),      self.key_ctrl_end)
        self.text.bind("<{}-period>".format(CtrlKey),   self.get_stop_sound)

        self.text.bind("<{}-BackSpace>".format(CtrlKey),   self.key_ctrl_backspace)
        self.text.bind("<{}-Delete>".format(CtrlKey),      self.key_ctrl_delete)

        # indentation

        self.text.bind("<{}-bracketright>".format(CtrlKey),    self.indent)
        self.text.bind("<{}-bracketleft>".format(CtrlKey),     self.unindent)

        # Toggle the menu

        self.text.bind("<{}-m>".format(CtrlKey), self.root.menu.toggle)

        # Key bindings to handle select
        self.text.bind("<Shift-Left>",  self.select_left)
        self.text.bind("<Shift-Right>", self.select_right)
        self.text.bind("<Shift-Up>",    self.select_up)
        self.text.bind("<Shift-Down>",  self.select_down)
        self.text.bind("<Shift-End>",   self.select_end)
        self.text.bind("<Shift-Home>",  self.select_home)
        self.text.bind("<{}-a>".format(CtrlKey), self.select_all)

        # Copy and paste key bindings

        self.text.bind("<{}-c>".format(CtrlKey), self.copy)
        self.text.bind("<{}-x>".format(CtrlKey), self.cut)
        self.text.bind("<{}-v>".format(CtrlKey), self.paste)

        # # Undo
        self.text.bind("<{}-z>".format(CtrlKey), self.undo)
        self.text.bind("<{}-y>".format(CtrlKey), self.redo)

        # Open a file

        self.text.bind("<{}-o>".format(CtrlKey), self.open)   

        # Switching buffers

        self.text.bind("<{}-Tab>".format(CtrlKey), self.cycle_buffer)                

        # Handling mouse events
        self.left_mouse = Mouse(self)
        self.text.bind("<Button-1>", self.mouse_press_left)
        self.text.bind("<B1-Motion>", self.mouse_left_drag)
        self.text.bind("<ButtonRelease-1>", self.mouse_left_release)
        self.text.bind("<Double-Button-1>", self.mouse_left_double_click)
        self.text.bind("<Button-2>" if SYSTEM==MAC_OS else "<Button-3>", self.mouse_press_right)
        self.text.bind("<Button-2>" if SYSTEM!=MAC_OS else "<Button-3>", lambda *e: "break") # disable middle button

        # select_background
        self.text.tag_configure(Tk.SEL, background=COLOURS["Background"])   # Temporary fix - set normal highlighting to background colour
        self.text.bind("<<Selection>>", self.selection)
        self.text.bind("<FocusOut>", self.de_select)

        # Allowed key-bindings

        self.text.bind("<{}-equal>".format(CtrlKey),  self.increase_font_size)
        self.text.bind("<{}-minus>".format(CtrlKey),  self.decrease_font_size)

        self.ignored_keys = (CtrlKey + "_L", CtrlKey + "_R", "sterling", "Shift_L", "Shift_R", "Escape")

        # Syntax

        self.whitespace = (" ", "\n")
        self.delimeters = (".", ",", "(", ")", "[","]","{", "}", "=")

        # Directional commands

        self.directions = ("Left", "Right", "Up", "Down", "Home", "End")

        self.handle_direction = {}
        self.handle_direction["Left"]  = self.key_left
        self.handle_direction["Right"] = self.key_right
        self.handle_direction["Down"]  = self.key_down
        self.handle_direction["Up"]    = self.key_up
        self.handle_direction["Home"]  = self.key_home
        self.handle_direction["End"]   = self.key_end

        # Selection indices
        self.sel_start = "0.0"
        self.sel_end   = "0.0"

        # Startup interpreter -- give interpreter information about this widget - i.e. console

        self.lang.start(out=self.console)

        # Only sync if told explicitly

        if self.sync_to_espgrid:
        
            self.lang.synchronise()

    def __str__(self):
        return "<Buffer - {}>".format(self.lang)

    # Sending to server
    # =================
    
    def send_message(self, message):
        """ Updates the MESSAGE object with the ID of this buffer then adds to send queue """
        if isinstance(message, list):
            for msg in message:
                self.send_message(msg)
        else:
            message.set_buf_id(self.id) 
            self.root.add_to_send_queue(message)
        return

    def send_operation(self, revision, operation):
        """ Called from textbox"""
        message = MSG_OPERATION(self.root.local_peer.id, operation.ops, revision)
        return self.send_message(message)

    def soft_reset(self):
        """ Sets the revision number to 0 and sets the document contents """
        self.text.revision = 0
        return

    def is_active(self):
        """ Returns True if this buffer contains the local peer """
        return self.root.local_peer.buf_id == self.id

    # Key press and operations
    # ========================

    def key_press(self, event):
        """ 'Pushes' the key-press to the server.
        """

        self.input_blocking = True

        # Ignore the CtrlKey and non-ascii chars

        if self.root.user_disabled(): # should be breaking

            self.input_blocking = False

            return "break"

        elif (event.keysym in self.ignored_keys):

            self.input_blocking = False

            return "break"

        elif event.keysym == "F4" and self.last_keypress == "Alt_L":

            self.input_blocking = False

            self.root.client.kill()

            return "break"

        # Get index

        index     = self.root.local_peer.get_index_num() # possibly just use .index_num
        line_num  = self.text.number_index_to_row_col(index)[0]
        doc_size  = len(self.text.read())
        tail      = doc_size - index
        selection = self.root.local_peer.selection_size()

        operation    = []
        index_offset = 0
        char         = None

        # Un-highlight any brackets

        self.remove_highlighted_brackets()

        # Key movement

        if event.keysym in self.directions:

            self.input_blocking = False

            return self.handle_direction.get(event.keysym, lambda: None).__call__()

        # Deleting a selected area

        elif selection and event.keysym in ("Delete", "BackSpace"):

            operation, index_offset = self.get_delete_selection_operation()

        # Deletion

        elif event.keysym == "Delete":

            if tail > 0:

                operation = self.new_operation(index, -1)

        elif event.keysym == "BackSpace":

            if index > 0:

                operation = self.new_operation(index - 1, -1)

                if tail > 0:

                    index_offset = -1

        # Inserting character

        else:

            if event.keysym == "Return":

                # If the line starts with blank space, add the same blank space

                char = "\n" + (" "*self.text.get_leading_whitespace(line_num))

            elif event.keysym == "Tab":

                char = " "*4

            else:

                char = event.char

            if len(char) > 0:

                if selection:

                    operation = self.new_operation(self.root.local_peer.select_start(), -selection, char)

                    index_offset = self.get_delete_selection_offset(char)

                else:

                    operation = self.new_operation(index, char)

                    index_offset = len(char)

        if operation:

            # Index offset is how much to *move* the label after the operation

            self.apply_operation(operation, index_offset)

            # If the character is a closing bracket, do some highlighting

            if char in self.text.right_brackets:

                self.text.highlight_brackets(char)

        # Remove any selected text

        self.de_select()

        # Store last key press for Alt+F4 etc

        self.last_keypress  = event.keysym

        self.input_blocking = False

        return "break"

    def remove_highlighted_brackets(self):
        """ Removes the text tag for highlighting brackets """
        return self.text.tag_remove("tag_open_brackets", "1.0", Tk.END)

    def new_operation(self, *ops):
        """ Returns a list of operations to apply to the document """
        return new_operation(*(list(ops) + [len(self.text.read())]))

    def get_delete_selection_operation(self):
        """ Returns an operation that deletes the selected area """
        op = self.new_operation(self.root.local_peer.select_start(), -self.root.local_peer.selection_size())
        offset = self.get_delete_selection_offset()
        return op, offset

    def get_delete_selection_offset(self, insert=""):
        """ Returns the index_offset for operations deleting the selected area. Use `insert` if you are
            inserting a character in place of the selected text """

        index = self.root.local_peer.get_index_num()
        sel_size = self.root.local_peer.selection_size()

        if index == self.root.local_peer.select_end():
            offset = len(insert) - sel_size
        elif index == self.root.local_peer.select_start():
            offset = len(insert)
        else:
            raise IndexError("Selection indices do not match")
        return offset

    def get_set_all_operation(self, text):
        """ Returns a new operation that deletes the contents then inserts the text """
        return [-len(self.text.read()), text]

    def apply_operation(self, operation, index_offset=0, **kwargs):
        """ Handles a text operation locally and sends to the server """

        if self.root.user_disabled() is False:

            # Apply locally

            self.text.apply_local_operation(operation, index_offset, **kwargs)

            # Handle the operation on the client side (this is just self.text.apply_client(operation) essentially)

            self.text.handle_operation(MSG_OPERATION(self.root.local_peer.id, operation, self.text.revision), client=True)

            # Reset the view on the textbox

            self.text.reset_view()

            # Make sure we can see the marker

            self.see_local_peer()

        return

    # Directional keypress
    # ====================

    def see_local_peer(self):
        """ Calculates the local peer tcl_index and makes sure the text widget views it """
        return self.see_peer(self.root.local_peer)

    def see_peer(self, peer):
        """ If the peer label (the peer's current tcl index +- 2 lines worth) is not 
            visible, make sure we can see it. """
        index        = peer.get_tcl_index()
        top_index    = "{}-2lines".format(index)
        bottom_index = "{}+2lines".format(index)
        if self.text.bbox(top_index) is None or self.text.bbox(bottom_index) is None:
            self.text.see(index)
        return

    def key_direction(self, move_func):
        """ Calls the function that moves the user's cursor then does necessary updating e.g. for server """
        self.see_local_peer()
        move_func()
        self.send_set_mark_msg()
        self.de_select()
        self.see_local_peer()
        return "break"

    def key_left(self):
        """ Called when the left arrow key is pressed; decreases the local peer index
            and updates the location of the label then sends a message to the server
            with the new location """
        return self.key_direction(self.move_marker_left)

    def key_right(self):
        """ Called when the right arrow key is pressed; increases the local peer index
            and updates the location of the label then sends a message to the server
            with the new location """
        return self.key_direction(self.move_marker_right)

    def key_down(self):
        """ Called when the down arrow key is pressed; increases the local peer index
            and updates the location of the label then sends a message to the server
            with the new location """
        return self.key_direction(self.move_marker_down)

    def key_up(self):
        """ Called when the up arrow key is pressed; decrases the local peer index
            and updates the location of the label then sends a message to the server
            with the new location """
        return self.key_direction(self.move_marker_up)

    def key_home(self):
        """ Called when the home key is pressed; sets the local peer location to 0
            and updates the location of the label then sends a message to the server
            with the new location """
        return self.key_direction(self.move_marker_home)

    def key_end(self):
        """ Called when the home key is pressed; sets the local peer location to 0
            and updates the location of the label then sends a message to the server
            with the new location """
        return self.key_direction(self.move_marker_end)

    def key_ctrl_home(self, event):
        """ Called when the user pressed Ctrl+Home. Sets the local peer index to 0 """
        return self.key_direction(self.move_marker_ctrl_home)

    def key_ctrl_end(self, event):
        """ Called when the user pressed Ctrl+End. Sets the local peer index to the end of the document """
        return self.key_direction(self.move_marker_ctrl_end)

    def key_ctrl_left(self, event):
        """ Called when the user pressed Ctrl+Left. Sets the local peer index to left of the previous word """
        return self.key_direction(self.move_marker_ctrl_left)

    def key_ctrl_right(self, event):
        """ Called when the user pressed Ctrl+Left. Sets the local peer index to right of the next word """
        return self.key_direction(self.move_marker_ctrl_right)

    # Deleting multiple characters

    def key_ctrl_backspace(self, event):
        """ Uses Ctrl+Left to move marker and delete the characters between """
        if self.root.local_peer.has_selection():
            op, offset = self.get_delete_selection_operation()
            self.de_select()
        else:
            index, _, new = self.root.local_peer.get_index_num(), self.move_marker_ctrl_left(), self.root.local_peer.get_index_num()
            if index == 0: # don't apply operation if we are at the start
                return "break"
            op, offset = self.new_operation(new, new - index), 0
        self.apply_operation(op, offset)
        return "break"

    def key_ctrl_delete(self, event):
        """ Uses Ctrl+Right to move marker and then delete the characters between """
        if self.root.local_peer.has_selection():
            op, offset = self.get_delete_selection_operation()
            self.de_select()
        else:
            len_text = len(self.text.read())
            index, _, new = self.root.local_peer.get_index_num(), self.move_marker_ctrl_right(), self.root.local_peer.get_index_num()
            if len_text == 0: # dont apply operation if there is no text
                return "break"
            op = self.new_operation(index, index - new)
            if new == len_text:
                offset = 0
            else:
                offset = index - new
        self.apply_operation(op, offset)
        return "break"


    # Moving the text marker
    # ======================

    def move_marker_left(self):
        """ Move the cursor right 1 place """
        self.root.local_peer.shift(-1)

    def move_marker_right(self):
        """ Move the cursor right 1 place """
        self.root.local_peer.shift(+1)

    def move_marker_up(self):
        """ Move the  cursor one line down """
        tcl_index  = self.text.number_index_to_tcl(self.root.local_peer.get_index_num())
        line_num   = int(tcl_index.split(".")[0])
        # Use the bounding box to adjust the y-pos
        # self.text.see(tcl_index)
        x, y, w, h = self.text.bbox(tcl_index)
        y = y - h
        # If the new index is off the canvas, try and see the line
        if y < 0:
            self.text.see(tcl_index + "-1lines")
            x, y, w, h = self.text.bbox(tcl_index)
            y = y - h
        if y > 0:
            new_index = self.text.tcl_index_to_number( self.text.index("@{},{}".format(x, y)) )
            self.root.local_peer.move(self.id, new_index)
        return

    def move_marker_down(self):
        """ Move the marker one line down """
        tcl_index = self.text.number_index_to_tcl(self.root.local_peer.get_index_num())
        # Use the bounding box to adjust the y-pos
        x, y, w, h = self.text.bbox(tcl_index)
        # If the line down is off screen, make sure we can see it
        if (y + (2 * h)) >= self.text.winfo_height():
            self.text.see(tcl_index + "+1lines") # View lines we can't see
        # Calculate new index and check bbox
        new_tcl_index = self.text.index("@{},{}".format(x, y + h))
        _, y1, _, _ = self.text.bbox(new_tcl_index)
        # Only move if the new line is different
        if y != y1:
            new_index = self.text.tcl_index_to_number( new_tcl_index )
            self.root.local_peer.move(self.id, new_index)
        return

    def move_marker_home(self):
        """ Moves the cursor to the beginning of a line """
        tcl_index = self.text.number_index_to_tcl(self.root.local_peer.get_index_num())
        x, y, w, h = self.text.bbox(tcl_index)
        index = self.text.tcl_index_to_number( self.text.index("@{},{}".format(1, y)) )
        self.root.local_peer.move(self.id, index)
        return

    def move_marker_end(self):
        """ Moves the cursor to the end of a line """
        tcl_index = self.text.number_index_to_tcl(self.root.local_peer.get_index_num())
        x, y, w, h = self.text.bbox(tcl_index)
        new_x = self.text.winfo_width()
        index = self.text.tcl_index_to_number( self.text.index("@{},{}".format(new_x, y)) ) # TODO: This goes one char short?
        self.root.local_peer.move(self.id, index)
        return

    def move_marker_ctrl_home(self):
        """ Moves the cursor the beginning of the document """
        self.root.local_peer.move(self.id, 0)
        return

    def move_marker_ctrl_end(self):
        """ Moves the cursor to the end of the document """
        self.root.local_peer.move(self.id, len(self.text.read()))
        return

    def move_marker_ctrl_left(self):
        """ Moves the cursor to the start of the current word"""
        index = self.get_word_left_index(self.root.local_peer.get_index_num())
        self.root.local_peer.move(self.id, index)
        return

    def move_marker_ctrl_right(self):
        """ Moves the cursor to the end of the current word, or next word if we are at the end.
            Left must be non-space, and right must be space"""
        index = self.get_word_right_index(self.root.local_peer.get_index_num())
        self.root.local_peer.move(self.id, index)
        return

    def get_word_left_index(self, index):
        """ Returns the index of the start of the current word """
        text  = self.text.read()
        # Don't look at the character before if it's a delimeter
        if index > 0 and text[index - 1] in (self.delimeters + self.whitespace):
            index -= 1
        for i in range(index, 0, -1):
            if text[i - 1] in self.delimeters and text[i] in self.delimeters:
                break
            elif text[i - 1] in (self.delimeters + self.whitespace) and text[i] not in (self.delimeters + self.whitespace):
                break
        else:
            i = 0
        return i

    def get_word_right_index(self, index):
        """ Returns the index of the end of the current word """
        text  = self.text.read()
        if index < len(text) and text[index] in (self.delimeters + self.whitespace):
            index += 1
        for i in range(index, len(text) - 1):
            if text[i - 1] in self.delimeters and text[i] in self.delimeters:
                break
            elif text[i - 1] not in (self.delimeters + self.whitespace) and text[i] in (self.delimeters + self.whitespace):
                break
        else:
            i = len(text)
        return i
        

    # Selection handling
    # ==================

    def de_select(self, event=None):
        """ If there is a selection, remove it and notify the server """
        notify = self.root.local_peer.de_select()
        if notify:
            self.send_select_msg()
        return

    def get_movement_index(self, move_func):
        """ Calls `move_func` and returns the index of the marker before and after the call """
        assert callable(move_func)
        start, _, end = self.root.local_peer.get_index_num(), move_func(), self.root.local_peer.get_index_num()
        return start, end

    def update_select(self, start, end):
        """ Updates the current selected area """

        # Update the selection
        self.root.local_peer.select(start, end)

        # Send info to server
        self.send_set_mark_msg()
        self.send_select_msg()

        # Update colours
        self.text.update_colours()

        return

    def select_left(self, event):
        """ Finds the currently selected portion of text of the local peer
            and the row/col to update it to and calls self.UpdateSelect  """

        self.update_select( *self.get_movement_index(self.move_marker_left) )

        return "break"

    def select_right(self, event):
        """ Finds the currently selected portion of text of the local peer
            and the row/col to update it to and calls self.UpdateSelect  """
            
        self.update_select( *self.get_movement_index(self.move_marker_right) )

        return "break"

    def select_up(self, event):
        """ Finds the currently selected portion of text of the local peer
            and the row/col to update it to and calls self.UpdateSelect  """

        self.update_select( *self.get_movement_index(self.move_marker_up) )

        return "break"

    def select_down(self, event):
        """ Finds the currently selected portion of text of the local peer
            and the row/col to update it to and calls self.UpdateSelect  """

        self.update_select( *self.get_movement_index(self.move_marker_down) )

        return "break"

    def select_end(self, event):
        """ Finds the currently selected portion of text of the local peer
            and the row/col to update it to and calls self.UpdateSelect  """

        self.update_select( *self.get_movement_index(self.move_marker_end) )

        return "break"

    def select_home(self, event):
        """ Finds the currently selected portion of text of the local peer
            and the row/col to update it to and calls self.UpdateSelect  """

        self.update_select( *self.get_movement_index(self.move_marker_home) )

        return "break"

    def select_all(self, event=None):
        """ Tells the server to highlight all the text in the editor and move
            the marker to 1,0 """

        self.root.local_peer.move(self.id, 0)
        self.update_select(0, len(self.text.read()))

        return "break"

    def selection(self, event=None):
        """ Overrides handling of selected areas """
        self.text.tag_remove(Tk.SEL, "1.0", Tk.END)
        return


    # Evaluating lines
    # ================

    def get_current_block(self):
        """ Finds the 'block' of code that the local peer is currently in
            and returns a tuple of the start and end row """
        return self.lang.get_block_of_code(self.text, self.root.local_peer.get_tcl_index())


    def single_line_evaluate(self, event=None):
        """ Finds contents of the current line and sends a message to each user (inc. this one) to evaluate """

        if self.input_blocking:

            # schedule

            self.after(50, lambda: self.evaluate(event))

        else:

            row, _ = self.text.number_index_to_row_col(self.root.local_peer.get_index_num())
            a, b   = "{}.0".format(row), "{}.end".format(row)

            if self.text.get(a, b).lstrip() != "":

                self.send_message( MSG_EVALUATE_BLOCK(self.root.local_peer.id, row, row) )

        return "break"

    def evaluate(self, event=None):
        """ Finds the current block of code to evaluate and tells the server """

        if self.input_blocking:

            # schedule

            self.after(50, lambda: self.evaluate(event))

        else:

            lines = self.get_current_block()

            a, b = ("%d.0" % n for n in lines)

            string = self.text.get( a , b ).lstrip()

            if string != "":

                #  Send notification to other peers

                msg = MSG_EVALUATE_BLOCK(self.root.local_peer.id, lines[0], lines[1])

                self.send_message( msg )

        return "break"

    # Font size
    # =========

    def change_font_size(self, amount):
        """ Updates the font sizes of the text based on `amount` which
            can be positive or negative """
        self.grid_propagate(False)
        for font in self.root.font_names:
            font = tkFont.nametofont(font)
            size = font.actual()["size"] + amount
            if size >= 8:

                font.configure(size=size)

                self.text.char_w = self.text.font.measure(" ")
                self.text.char_h = self.text.font.metrics("linespace")

                shift = 2 * (1 if amount > 0 else -1)

                self.line_numbers.config(width=self.line_numbers.winfo_width() + shift)

                self.text.refresh_peer_labels()

        return

    def decrease_font_size(self, event):
        """ Calls `self.ChangeFontSize(-1)` and then resizes the line numbers bar accordingly """
        self.change_font_size(-1)
        return 'break'

    def increase_font_size(self, event=None):
        """ Calls `self.ChangeFontSize(+1)` and then resizes the line numbers bar accordingly """
        self.change_font_size(+1)
        return 'break'

    # Mouse Clicks
    # ============

    def mouse_press_left(self, event):
        """ Updates the server on where the local peer's marker is when the mouse release event is triggered.
            Selected area is removed un-selected. """

        # If we click somewhere, remove the closed brackets tag

        self.remove_highlighted_brackets() 

        # Get location and process

        index = self.left_mouse.click(event)

        self.root.local_peer.move(self.id, index)

        self.de_select()

        self.send_message( MSG_SET_MARK(self.root.local_peer.id, index) )

        # Make sure the text box gets focus

        self.text.focus_set()

        return "break"

    def mouse_left_release(self, event=None):
        """ Updates the server on where the local peer's marker is when the mouse release event is triggered """

        index = self.left_mouse.release(event)

        self.root.local_peer.move(self.id, index)

        self.send_message( MSG_SET_MARK(self.root.local_peer.id, index) )

        # Make sure the text box gets focus

        self.text.focus_set()

        #self.text.tag_remove(SEL, "1.0", END) # Remove any *actual* selection to stop scrolling

        return "break"

    def mouse_left_drag(self, event):
        """ Updates the server with the portion of selected text """
        if self.left_mouse.is_pressed:

            start = self.left_mouse.anchor
            end   = self.left_mouse.click(event)

            self.update_select(start, end) # sends message to server

        return "break"

    def mouse_left_double_click(self, event):
        """ Highlights word - not yet implemented """
        index = self.left_mouse.click(event)
        right = self.get_word_right_index(index)
        left  = self.get_word_left_index(index)
        self.update_select(left, right)
        return "break"

    def mouse_press_right(self, event):
        """ Displays popup menu"""
        self.popup.show(event)
        return "break"

    # Copy, paste, undo etc
    # =====================

    def undo(self, event=None):
        ''' Triggers an undo event '''
        if len(self.text.undo_stack):
            op = self.text.get_undo_operation()
            self.apply_operation(self.new_operation(*op.ops), index=get_operation_index(op.ops), undo=True)
        return "break"

    def redo(self, event=None):
        ''' Re-applies the last undo event '''
        if len(self.text.redo_stack):
            op = self.text.get_redo_operation()
            self.apply_operation(self.new_operation(*op.ops), index=get_operation_index(op.ops), redo=True)
        return "break"

    def open(self, event=None):
        ''' Opens the  open file window, and imports the text indo the buffer tab - replacing everything '''

        fn = tkFileDialog.askopenfilename()

        try:

            with open(fn) as f:

                self.apply_operation(self.get_set_all_operation(f.read()))

        except Exception as e:

            tkMessageBox.showwarning("Failed to open file", "Could not open file '{}'.\n\n{}".format(fn, str(e)))

        return "break"

    def copy(self, event=None):
        ''' Copies selected text to the clipboard '''
        if self.root.local_peer.has_selection():
            text = self.text.read()[self.root.local_peer.select_start():self.root.local_peer.select_end()]
            self.winfo_toplevel().clipboard_clear()
            self.winfo_toplevel().clipboard_append(text)
        return "break"

    def cut(self, event=None):
        ''' Copies selected text to the clipboard and then deletes it'''
        if self.root.local_peer.has_selection():
            text = self.text.read()[self.root.local_peer.select_start():self.root.local_peer.select_end()]

            self.winfo_toplevel().clipboard_clear()
            self.winfo_toplevel().clipboard_append(text)

            start_point = self.root.local_peer.select_start()

            operation = self.new_operation(start_point, -self.root.local_peer.selection_size())

            self.apply_operation(operation)

            self.de_select()

            self.root.local_peer.move(self.id, start_point)

        return "break"

    def paste(self, event=None):
        """ Inserts text from the clipboard """

        try:

            text = self.winfo_toplevel().clipboard_get()

        except Tk.TclError:

            return "break"

        if len(text):

            # If selected, delete that first
            if self.root.local_peer.has_selection():

                selection = self.root.local_peer.selection_size()

                operation = self.new_operation(self.root.local_peer.select_start(), -selection, text)

                offset = self.get_delete_selection_offset(text)

                self.apply_operation(operation, index_offset=offset)

                self.de_select()

            else:

                operation = self.new_operation(self.root.local_peer.get_index_num(), text)

                self.apply_operation(operation, index_offset=len(text))

        return "break"

    def indent(self, event=None):
        return "break"

    def unindent(self, event=None):
        return "break"

    def send_set_mark_msg(self):
        """ Sends a message to server with the location of this peer """
        self.send_message(MSG_SET_MARK(self.root.local_peer.id, self.root.local_peer.get_index_num(), reply=0))
        return

    def send_select_msg(self):
        """ Sends a message to server with the location of this peer """
        self.send_message(MSG_SELECT(self.root.local_peer.id, self.root.local_peer.select_start(), self.root.local_peer.select_end(), reply=0))
        return

    def redraw(self):
        """ Calls any redraw method e.g. line numbers """
        if self.frame_count == self.frame_reset:
            self.line_numbers.redraw()
            self.frame_count = 0
        self.frame_count += 1
        return

    def cycle_buffer(self, event=None):
        """ Moves the cursor to the next text buffer """
        
        new_id = (self.id + 1) % len(self.root.buffers)
        new_buf = self.root.buffers[new_id]

        # Remove any bracket highlighting

        self.remove_highlighted_brackets()
        self.de_select()

        # Get location and process

        self.root.local_peer.move(new_id, 0)

        new_buf.send_message( MSG_SET_MARK(self.root.local_peer.id, 0) )

        new_buf.text.focus_set()

        return "break"

    # Language dependent commands
    def get_stop_sound(self, *event):
        """ Sends a kill all sound message to the server based on the language """
        string = DEFAULT_INTERPRETERS[self.id].get_stop_sound()
        self.send_message( MSG_EVALUATE_STRING(self.root.local_peer.id, string, reply=1) )
        return "break"