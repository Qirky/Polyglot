from __future__ import absolute_import

from .tkimport import Tk, tkMessageBox, tkFileDialog

from .interface import ROOT
from ..interpreter import DEFAULT_INTERPRETERS, DummyInterpreter

import functools

class ConnectionInput:
    """ Interface for getting connection info from the user """
    def __init__(self, client, get_info=True, **kwargs):

        self.client  = client
        self.using_gui_input = get_info
        self.options = kwargs
        self.root=ROOT

        # If there is all the info, go straight to main interface

        if self.using_gui_input:

            self.root.title("Polyglot")
            self.root.protocol("WM_DELETE_WINDOW", self.quit )
            self.root.resizable(False, False)
            
            # Host
            lbl = Tk.Label(self.root, text="Host:")
            lbl.grid(row=0, column=0, stick=Tk.W)
            self.host=Tk.Entry(self.root)
            self.host.insert(0, kwargs.get("host", "localhost"))
            self.host.grid(row=0, column=1, sticky=Tk.NSEW)

            # Port
            lbl = Tk.Label(self.root, text="Port:")
            lbl.grid(row=1, column=0, stick=Tk.W)
            self.port=Tk.Entry(self.root)
            self.port.insert(0, kwargs.get("port", "57890"))
            self.port.grid(row=1, column=1, sticky=Tk.NSEW)
            
            # Name
            lbl = Tk.Label(self.root, text="Name:")
            lbl.grid(row=2, column=0, sticky=Tk.W)
            self.name=Tk.Entry(self.root)
            self.name.grid(row=2, column=1, sticky=Tk.NSEW)
            
            # Password
            lbl = Tk.Label(self.root, text="Password: ")
            lbl.grid(row=3, column=0, sticky=Tk.W)
            self.password=Tk.Entry(self.root, show="*")
            self.password.grid(row=3, column=1, sticky=Tk.NSEW)

            # Interpreter choice
            frame = Tk.LabelFrame(self.root, text="Active Languages", padx=10, pady=5)
            frame.grid(row=4, column=0, sticky=Tk.NSEW, columnspan=2)

            lbl = Tk.Label(frame, text="Active")
            lbl.grid(row = 0, column = 1, sticky=Tk.NSEW)
            lbl = Tk.Label(frame, text="Sync")
            lbl.grid(row = 0, column = 2, sticky=Tk.NSEW)

            frame.grid_columnconfigure(1, weight=1)
            frame.grid_columnconfigure(2, weight=1)

            self.checkboxes = {}

            for lang_id, lang in DEFAULT_INTERPRETERS.items(): 

                # Label

                row_id = lang_id + 1

                lbl = Tk.Label(frame, text=lang.name)
                lbl.grid(row=row_id, column = 0, stick=Tk.W)

                # Active

                var1 = Tk.IntVar()
                var1.set(1)
                box1 = Tk.Checkbutton(frame, variable=var1)
                box1.var = var1
                box1.grid(row=row_id, column=1, sticky=Tk.NSEW)

                # Sync

                var2 = Tk.IntVar()
                var2.set(1)
                box2 = Tk.Checkbutton(frame, variable=var2)
                box2.var = var2
                box2.grid(row=row_id, column=2, sticky=Tk.NSEW)

                # Set up boxes to have tick/un-tick the other appropriately

                box1.config(command = functools.partial(lambda x, y: x.var.set(0) if y.var.get() == 0 else None, box2, box1))
                box2.config(command = functools.partial(lambda x, y: x.var.set(1) if y.var.get() == 1 else y.var.set(0), box1, box2))

                self.checkboxes[lang_id] = (box1, box2)


            # Ok button
            self.button=Tk.Button(self.root, text='Ok',command=self.store_data)
            self.button.grid(row=5, column=0, columnspan=2, sticky=Tk.NSEW)

            self.response = Tk.StringVar()
            self.lbl_response=Tk.Label(self.root, textvariable=self.response, fg="Red")
            self.lbl_response.grid(row=6, column=0, columnspan=2)
            self.lbl_response.grid_remove()
            
            # Value
            self.data = {}
            
            # Enter shortcut
            self.root.bind("<Return>", self.store_data)

    def start(self):
        if self.using_gui_input:
            self.center()
            self.mainloop() # calls finish from the OK button
        else:
            self.finish()

    def mainloop(self):        
        if self.client.mainloop_started is False:
            try:
                self.client.mainloop_started = True
                self.root.mainloop()
            except KeyboardInterrupt:
                self.client.kill()
        return

    def quit(self):
        self.data = {}
        return self.root.quit()

    def finish(self):
        """ Starts the client connection"""
        self.root.unbind("<Return>")
        self.client.setup(**self.options)
        return

    def cleanup(self):
        """ Removes all the widgets from the root """
        if self.using_gui_input:
            for widget in self.root.winfo_children():
                widget.grid_forget()
        return

    def select_path(self, lang):
        """ If lang is select_path_option, open file dialog and set self.lang to the path """
        if lang == self.select_path_option:
            path = tkFileDialog.askopenfilename(initialdir = "/",title = "Select file")
            self.lang.set(path)
        return

    def store_data(self, event=None):
        """ Stores the data in the entry fields then closes the window """
        host = self.host.get()
        port = self.port.get()
        name = self.name.get()
        password = self.password.get()

        # Use dummy interpreter for un-checked boxes

        lang_data = {}

        for lang_id, checkboxes in self.checkboxes.items():

            active_box, sync_box = checkboxes

            # Get info on sync to EspGrid

            sync_to_esp = bool(sync_box.var.get())
        
            if active_box.var.get() == 1:

                interpreter = DEFAULT_INTERPRETERS[lang_id]

            else:

                interpreter = DummyInterpreter

            lang_data[lang_id] = (interpreter, sync_to_esp)

        # If we have values for name, host, and port then go to "finish"

        if name.strip() != "" and host.strip() != "" and port.strip() != "":

            self.options.update(  
                host = host, 
                port = port, 
                name = name, 
                password = password,
                lang = lang_data
            )

            self.finish()

        return

    def center(self):
        """ Centers the popup in the middle of the screen """
        self.root.update_idletasks()
        w = self.root.winfo_screenwidth()
        h = self.root.winfo_screenheight()
        size = tuple(int(_) for _ in self.root.geometry().split('+')[0].split('x'))
        x = int(w/2 - size[0]/2)
        y = int(h/2 - size[1]/2)
        self.root.geometry("+{}+{}".format(x, y))
        self.lbl_response.config(wraplength=size[0])
        self.name.focus()
        return        

    def print_message(self, message):
        """ Displays the response message to the user """
        if self.using_gui_input:
            self.response.set(message)
            self.lbl_response.grid()
        else:
            print(message)
        return
