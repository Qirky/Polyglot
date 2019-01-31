from __future__ import absolute_import
from .tkimport import Tk

class Dragbar(Tk.Frame):
    cursor_style="sb_v_double_arrow"
    def __init__(self, parent, *args, **kwargs):

        self.parent = parent # buffer
        self.root   = parent.root # interface

        kwargs["cursor"]=self.cursor_style

        Tk.Frame.__init__( self, self.parent, **kwargs )

        self.mouse_down = False
        
        self.bind("<Button-1>",        self.drag_mouseclick)        
        self.bind("<ButtonRelease-1>", self.drag_mouserelease)
        self.bind("<B1-Motion>",       self.drag_mousedrag)

    def drag_mouseclick(self, event):
        """ Allows the user to resize the console height """
        self.mouse_down = True
        self.parent.grid_propagate(False)
        return
    
    def drag_mouserelease(self, event):
        self.mouse_down = False
        self.root.active_buffer().text.focus_set()
        return

    def drag_mousedrag(self, event):
        if self.mouse_down:

            line_height = self.parent.text.char_h

            text_height = ( self.parent.text.winfo_height() / line_height ) # In lines

            widget_y = self.parent.console.winfo_rooty() # Location of the console

            new_height =  ( self.parent.console.winfo_height() + (widget_y - event.y_root) )

            # Update heights of console

            self.parent.console.config(height = int(max(2, new_height / line_height)))

        return "break"

class VerticalDragbar(Tk.Frame):
    cursor_style="sb_h_double_arrow"
    def __init__(self, root, main, sub, *args, **kwargs):

        self.root   = root # interface
        self.parent = root.buffer_frame # frame for buffers
        self.buf1 = main # buffer
        self.buf2 = sub

        kwargs["cursor"]=self.cursor_style

        Tk.Frame.__init__( self, self.parent, **kwargs )

        self.mouse_down = False
        
        self.bind("<Button-1>",        self.drag_mouseclick)        
        self.bind("<ButtonRelease-1>", self.drag_mouserelease)
        self.bind("<B1-Motion>",       self.drag_mousedrag)

    def drag_mouseclick(self, event):
        """ Allows the user to resize the console height """
        self.mouse_down = True
        self.parent.grid_propagate(False)
        return
    
    def drag_mouserelease(self, event):
        self.mouse_down = False
        self.root.active_buffer().text.focus_set()
        return

    def drag_mousedrag(self, event):
        """ Resize the canvas """
        if self.mouse_down:

            # Main buffer

            width1 = self.buf1.winfo_width()
            width2 = self.buf2.winfo_width()
            delta  = event.x

            new_width = width1 + delta

            self.buf1.config(width=int(new_width))

            new_width  = width2 - delta

            self.buf2.config(width=int(new_width))

            self.winfo_toplevel().update_idletasks()

        return "break"
