"""
    Interpreter
    -----------

    Runs a block of FoxDot code. Designed to be overloaded
    for other language communication

"""
from __future__ import absolute_import
from .config import *

from subprocess import Popen
from subprocess import PIPE, STDOUT
from datetime import datetime

# Import OSC library depending on Python version

if PY_VERSION == 2:
    from . import OSC
else:
    from . import OSC3 as OSC

try:
    broken_pipe_exception = BrokenPipeError
except NameError:  # Python 2
    broken_pipe_exception = IOError

CREATE_NO_WINDOW = 0x08000000 if SYSTEM == WINDOWS else 0

import sys
import re
import time
import threading
import shlex
import tempfile
import os, os.path

DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

def compile_regex(kw):
    """ Takes a list of strings and returns a regex that
        matches each one """
    return re.compile(r"(?<![a-zA-Z.])(" + "|".join(kw) + ")(?![a-zA-Z])")

SEPARATOR = ":"; _ = " %s " % SEPARATOR

def colour_format(text, colour):
    return '<colour="{}">{}</colour>'.format(colour, text)

## dummy interpreter

class DummyInterpreter:
    stop_sound = ""
    lang = None
    def __init__(self, *args, **kwargs):
        self.re={}

    def __repr__(self):
        return repr(self.__class__.__name__)

    def get_block_of_code(self, text, index):
        """ Returns the start and end line numbers of the text to evaluate when pressing Ctrl+Return. """

        # Get start and end of the buffer
        start, end = "1.0", text.index("end")
        lastline   = int(end.split('.')[0]) + 1

        # Indicies of block to execute
        block = [0,0]        
        
        # 1. Get position of cursor
        cur_x, cur_y = index.split(".")
        cur_x, cur_y = int(cur_x), int(cur_y)
        
        # 2. Go through line by line (back) and see what it's value is
        
        for line in range(cur_x, 0, -1):
            if not text.get("%d.0" % line, "%d.end" % line).strip():
                break

        block[0] = line

        # 3. Iterate forwards until we get two \n\n or index==END
        for line in range(cur_x, lastline):
            if not text.get("%d.0" % line, "%d.end" % line).strip():
                break

        block[1] = line

        return block

    def is_active(self):
        """ Returns true if not using a dummer interpreter """
        return self.lang is not None
    
    def evaluate(self, string, *args, **kwargs):
        self.print_stdin(string, *args, **kwargs)
        return

    def start(self, out=None):
        if out is not None:
            self.console = out
        return self
    
    def stdout(self, *args, **kwargs):
        pass
    
    def kill(self, *args, **kwargs):
        pass
    
    def print_stdin(self, string, name=None, colour="White"):
        """ Handles the printing of the execute code to screen with coloured
            names and formatting """
        # Split on newlines
        string = [line.replace("\n", "") for line in string.split("\n") if len(line.strip()) > 0]
        if len(string) > 0 and name is not None:
            name = str(name)
            self.console.write(colour_format(name, colour) + _ + string[0])
            # Use ... for the remainder  of the  lines
            n = len(name)
            for i in range(1,len(string)):
                self.console.write(colour_format("." * n, colour) + _ + string[i])
                self.console.flush()
        return

    def synchronise(self):
        """ Execute code for synchronising to EspGrid. Overloaded in sub-classes. """
        return
    
    @classmethod
    def get_stop_sound(cls):
        """ Returns the string for stopping all sound in a language """
        return cls.stop_sound
    
    @staticmethod
    def format(string):
        """ Method to be overloaded in sub-classes for formatting strings to be evaluated """
        return string
    
class Interpreter(DummyInterpreter):
    lang     = None
    clock    = None
    bootfile = None
    keyword_regex = compile_regex([])
    comment_regex = compile_regex([])
    stdout   = None
    stdout_thread = None
    filetype = ".txt"
    bootstrap = None
    def __init__(self, path, args=""):

        self.re = {"tag_bold": self.find_keyword, "tag_italic": self.find_comment}

        self.path = shlex.split(path)

        self.args = self._get_args(args)

        self.f_out = tempfile.TemporaryFile("w+", 1) # buffering = 1
        self.is_alive = True

        self.console = sys.stdout # can be overwritten
        self.is_reading_from_stdout = False

        self.setup()

    @staticmethod
    def _get_args(args):
        if isinstance(args, str):
    
            args = shlex.split(args)

        elif isinstance(args, list) and len(args) == 1:

            args = shlex.split(args[0])

        return args

    def setup(self):
        """ Overloaded in sub-classes """
        return

    def start(self, *args, **kwargs):
        """ Opens the process with the interpreter language """

        DummyInterpreter.start(self, *args, **kwargs)

        try:
        
            self.lang = Popen(self.path + self.args, shell=False, universal_newlines=True, bufsize=1,
                              stdin=PIPE,
                              stdout=self.f_out,
                              stderr=self.f_out,
    						  creationflags=CREATE_NO_WINDOW)

            self.stdout_thread = threading.Thread(target=self.stdout)
            self.stdout_thread.start()

        except FileNotFoundError:

            raise ExecutableNotFoundError(self.get_path_as_string())

        # Load bootfile

        if self.bootstrap is not None:

            for line in self.bootstrap.split("\n"):

                self.lang.stdin.write(line.rstrip() + "\n")
                self.lang.stdin.flush()

        return self

    def get_path_as_string(self):
        """ Returns the executable input as a string """
        return " ".join(self.path)

    def find_keyword(self, string):
        return [(match.start(), match.end()) for match in self.keyword_regex.finditer(string)]

    def find_comment(self, string):
        return [(match.start(), match.end()) for match in self.comment_regex.finditer(string)]

    def write_stdout(self, string):
        """ Write text to the language process stdin """
        if self.is_alive:
            self.lang.stdin.write(self.format(string))
            self.lang.stdin.flush()
        return

    def evaluate(self, string, *args, **kwargs):
        """ Sends a string to the stdin and prints the text to the console """
        # Print to console
        self.print_stdin(string, *args, **kwargs)
        # Pipe to the subprocess
        self.write_stdout(string)
        # Read from subprocess after 0.1 sec
        # def read():
        #     time.sleep(0.05)
        #     self.read_from_stdout()
        # threading.Thread(target=read).start()
        return

    def stdout(self, text=""):
        """ Continually reads the stdout from the self.lang process """
        while self.is_alive:
            if self.lang.poll():
                self.is_alive = False
                break
            try:
                response = self.read_from_stdout()
                # Send the response
                if response:
                    self.console.root.send_console_message(response)
                time.sleep(0.1)
            except ValueError as e:
                print(e)
                return
        return

    def read_from_stdout(self):
        if self.is_reading_from_stdout is False:
            self.is_reading_from_stdout = True
            # Store the text response
            response = []
            # Check contents of file
            self.f_out.seek(0)
            for stdout_line in iter(self.f_out.readline, ""):
                response.append( stdout_line.rstrip() )
                self.console.write(response[-1]) 
            # clear tmpfile
            self.f_out.truncate(0)
            self.is_reading_from_stdout = False
        return "\n".join(response)

    def kill(self):
        """ Stops communicating with the subprocess """
        # End process if not done so already
        self.is_alive = False
        if self.lang.poll() is None:
            self.lang.communicate()

class BuiltinInterpreter(Interpreter):
    def __init__(self):
        Interpreter.__init__(self, self.path)

class FoxDotInterpreter(BuiltinInterpreter):
    name = "FoxDot"
    stop_sound = "Clock.clear()"
    filetype=".py"
    path = "{} -u -m FoxDot --pipe".format(PYTHON_EXECUTABLE)
    id = 0

    def setup(self):
        self.keywords = ["Clock", "Scale", "Root", "var", "linvar", '>>']
        self.keyword_regex = compile_regex(self.keywords)

    def synchronise(self):
        self.evaluate("Clock.latency=0.2")
        self.evaluate("Clock.sync_to_espgrid()")
        return

    def __repr__(self):
        return "FoxDot"

    @staticmethod
    def format(string):
        return "{}\n\n".format(string)

    @classmethod
    def find_comment(cls, string):        
        instring, instring_char = False, ""
        for i, char in enumerate(string):
            if char in ('"', "'"):
                if instring:
                    if char == instring_char:
                        instring = False
                        instring_char = ""
                else:
                    instring = True
                    instring_char = char
            elif char == "#":
              if not instring:
                  return [(i, len(string))]
        return []

    def kill(self):
        self.evaluate(self.get_stop_sound())
        Interpreter.kill(self)
        return

class TidalInterpreter(BuiltinInterpreter):
    name = "TidalCycles"
    path = 'ghci'
    filetype = ".tidal"
    stop_sound = "hush"
    id = 1

    def start(self, *args, **kwargs):

        # Import boot up code

        from .boot.tidal import bootstrap

        self.bootstrap = bootstrap

        # Set any keywords e.g. d1 and $

        self.keywords  = ["d{}".format(n) for n in range(1,17)] # update
        self.keywords.extend( ["\$", "#", "hush"] )

        self.keyword_regex = compile_regex(self.keywords)

        # Start

        Interpreter.start(self, *args, **kwargs)
        
        return self

    def __repr__(self):
        return "TidalCycles"

    def synchronise(self):
        return self.evaluate("espgrid tidal")

    @classmethod
    def find_comment(cls, string):        
        instring, instring_char = False, ""
        for i, char in enumerate(string):
            if char in ('"', "'"):
                if instring:
                    if char == instring_char:
                        instring = False
                        instring_char = ""
                else:
                    instring = True
                    instring_char = char
            elif char == "-":
                if not instring and (i + 1) < len(string) and string[i + 1] == "-":
                    return [(i, len(string))]
        return []
    
    @staticmethod
    def format(string):
        """ Used to formant multiple lines in haskell """
        return ":{\n"+string+"\n:}\n"

class StackTidalInterpreter(TidalInterpreter):
    path = "stack ghci"

# Interpreters over OSC (e.g. Sonic Pi)
# -------------------------------------

class OSCInterpreter(Interpreter):
    """ Class for sending messages via OSC instead of using a subprocess """
    def __init__(self):
        self.re = {"tag_bold": self.find_keyword, "tag_italic": self.find_comment}
        self.client = OSC.OSCClient()
        self.client.connect((self.host, self.port))

    # Overload to not activate a server
    def start(self, *args, **kwargs):
        return DummyInterpreter.start(self, *args, **kwargs)

    def kill(self):
        self.evaluate(self.get_stop_sound())
        self.client.close()
        return

    def new_osc_message(self, string):
        """ Overload in sub-class, return OSC.OSCMessage"""
        return

    def evaluate(self, string, *args, **kwargs):
        # Print to the console the message
        Interpreter.print_stdin(self, string, *args, **kwargs)
        # Create an osc message and send to the server
        self.client.send(self.new_osc_message(string))
        return

# Old OSC Interpreter

class SuperColliderInterpreter(OSCInterpreter):
    name = "SuperCollider"
    stop_sound = "s.freeAll"
    filetype = ".scd"
    host = 'localhost'
    port = 57120
    id = 2

    def __repr__(self):
        return "SuperCollider"

    def new_osc_message(self, string):
        """ Returns OSC message for Troop Quark """
        msg = OSC.OSCMessage("/troop")
        msg.append([string])
        return msg

    def synchronise(self):
        self.evaluate("s.latency=0.2")
        self.evaluate("TempoClock.default = EspClock.new")
        return

    @classmethod
    def find_comment(cls, string):        
        instring, instring_char = False, ""
        for i, char in enumerate(string):
            if char in ('"', "'"):
                if instring:
                    if char == instring_char:
                        instring = False
                        instring_char = ""
                else:
                    instring = True
                    instring_char = char
            elif char == "/":
                if not instring and i < len(string) and string[i + 1] == "/":
                    return [(i, len(string))]
        return []

    def get_block_of_code(self, text, index):
        """ Returns the start and end line numbers of the text to evaluate when pressing Ctrl+Return. """

        # Get start and end of the buffer
        start, end = "1.0", text.index("end")
        lastline   = int(end.split('.')[0]) + 1

        # Indicies of block to execute
        block = [0,0]        
        
        # 1. Get position of cursor
        cur_y, cur_x = index.split(".")
        cur_y, cur_x = int(cur_y), int(cur_x)

        left_cur_y, left_cur_x   = cur_y, cur_x
        right_cur_y, right_cur_x = cur_y, cur_x

        # Go back to find a left bracket

        while True:

            new_left_cur_y,  new_left_cur_x  = self.get_left_bracket(text, left_cur_y, left_cur_x)
            new_right_cur_y, new_right_cur_x = self.get_right_bracket(text, right_cur_y, right_cur_x)

            if new_left_cur_y is None or new_right_cur_y is None:

                block = [left_cur_y, right_cur_y + 1]

                break

            else:

                left_cur_y,  left_cur_x  = new_left_cur_y,  new_left_cur_x
                right_cur_y, right_cur_x = new_right_cur_y, new_right_cur_x

        return block

    def get_left_bracket(self, text, cur_y, cur_x):
        count = 0
        line_text = text.get("{}.{}".format(cur_y, 0), "{}.{}".format(cur_y, "end"))
        for line_num in range(cur_y, 0, -1):
            # Only check line if it has text
            if len(line_text) > 0:
                for char_num in range(cur_x - 1, -1, -1):
                    
                    try:
                        char = line_text[char_num] 
                    except IndexError as e:
                        print("left bracket, string is {}, index is {}".format(line_text, char_num))
                        raise(e)

                    if char == ")":
                        count += 1
                    elif char == "(":
                        if count == 0:
                            return line_num, char_num
                        else:
                            count -= 1
            line_text = text.get("{}.{}".format(line_num - 1, 0), "{}.{}".format(line_num - 1, "end"))
            cur_x     = len(line_text)
        return None, None

    def get_right_bracket(self, text, cur_y, cur_x):
        num_lines = int(text.index("end").split(".")[0]) + 1
        count = 0
        for line_num in range(cur_y, num_lines):
            line_text = text.get("{}.{}".format(line_num, 0), "{}.{}".format(line_num, "end"))
            # Only check line if it has text
            if len(line_text) > 0:
                for char_num in range(cur_x, len(line_text)):
                    
                    try:
                        char = line_text[char_num] 
                    except IndexError as e:
                        print("right bracket, string is {}, index is {}".format(line_text, char_num))
                        raise(e)

                    if char == "(":
                        count += 1
                    if char == ")":
                        if count == 0:
                            return line_num, char_num + 1
                        else:
                            count -= 1
            cur_x = 0
        else:
            return None, None

# Work in progress sc interpreter            

class _SuperColliderInterpreter(BuiltinInterpreter, OSCInterpreter):
    name = "SuperCollider"
    path = ""
    stop_sound = "s.freeAll"
    filetype = ".scd"
    host = 'localhost'
    port = 57120
    id = 2
    def __init__(self, *args, **kwargs):
        BuiltinInterpreter.__init__(self, *args, **kwargs)
        OSCInterpreter.__init__(self, *args, **kwargs)

    def __repr__(self):
        return "SuperCollider"

    def start(self, *args, **kwargs):
        """ Need to find the path for sclang and give it a startup file """

        # Boot supercollider and read from it

        from .boot import supercollider

        sc_path = supercollider.find_path()

        fn_path = supercollider.get_startup_file(True, False) # TODO update with FoxDot and Tidal information

        os.chdir(os.path.dirname(sc_path))

        self.path = [sc_path, fn_path]

        # Listen from the process

        BuiltinInterpreter.start(self, *args, **kwargs)

        # Send messages to the OSC

        OSCInterpreter.start(self, *args, **kwargs)

    def kill(self):
        BuiltinInterpreter.kill(self)
        # OSCInterpreter.kill(self)
        return

    def new_osc_message(self, string):
        """ Returns OSC message for Troop Quark """
        msg = OSC.OSCMessage("/troop")
        msg.append([string])
        return msg

    def synchronise(self):
        self.evaluate("s.latency=0.2")
        self.evaluate("TempoClock.default = EspClock.new")
        return

    @classmethod
    def find_comment(cls, string):        
        instring, instring_char = False, ""
        for i, char in enumerate(string):
            if char in ('"', "'"):
                if instring:
                    if char == instring_char:
                        instring = False
                        instring_char = ""
                else:
                    instring = True
                    instring_char = char
            elif char == "/":
                if not instring and i < len(string) and string[i + 1] == "/":
                    return [(i, len(string))]
        return []

    def get_block_of_code(self, text, index):
        """ Returns the start and end line numbers of the text to evaluate when pressing Ctrl+Return. """

        # Get start and end of the buffer
        start, end = "1.0", text.index("end")
        lastline   = int(end.split('.')[0]) + 1

        # Indicies of block to execute
        block = [0,0]        
        
        # 1. Get position of cursor
        cur_y, cur_x = index.split(".")
        cur_y, cur_x = int(cur_y), int(cur_x)

        left_cur_y, left_cur_x   = cur_y, cur_x
        right_cur_y, right_cur_x = cur_y, cur_x

        # Go back to find a left bracket

        while True:

            new_left_cur_y,  new_left_cur_x  = self.get_left_bracket(text, left_cur_y, left_cur_x)
            new_right_cur_y, new_right_cur_x = self.get_right_bracket(text, right_cur_y, right_cur_x)

            if new_left_cur_y is None or new_right_cur_y is None:

                block = [left_cur_y, right_cur_y + 1]

                break

            else:

                left_cur_y,  left_cur_x  = new_left_cur_y,  new_left_cur_x
                right_cur_y, right_cur_x = new_right_cur_y, new_right_cur_x

        return block

    def get_left_bracket(self, text, cur_y, cur_x):
        count = 0
        line_text = text.get("{}.{}".format(cur_y, 0), "{}.{}".format(cur_y, "end"))
        for line_num in range(cur_y, 0, -1):
            # Only check line if it has text
            if len(line_text) > 0:
                for char_num in range(cur_x - 1, -1, -1):
                    
                    try:
                        char = line_text[char_num] 
                    except IndexError as e:
                        print("left bracket, string is {}, index is {}".format(line_text, char_num))
                        raise(e)

                    if char == ")":
                        count += 1
                    elif char == "(":
                        if count == 0:
                            return line_num, char_num
                        else:
                            count -= 1
            line_text = text.get("{}.{}".format(line_num - 1, 0), "{}.{}".format(line_num - 1, "end"))
            cur_x     = len(line_text)
        return None, None

    def get_right_bracket(self, text, cur_y, cur_x):
        num_lines = int(text.index("end").split(".")[0]) + 1
        count = 0
        for line_num in range(cur_y, num_lines):
            line_text = text.get("{}.{}".format(line_num, 0), "{}.{}".format(line_num, "end"))
            # Only check line if it has text
            if len(line_text) > 0:
                for char_num in range(cur_x, len(line_text)):
                    
                    try:
                        char = line_text[char_num] 
                    except IndexError as e:
                        print("right bracket, string is {}, index is {}".format(line_text, char_num))
                        raise(e)

                    if char == "(":
                        count += 1
                    if char == ")":
                        if count == 0:
                            return line_num, char_num + 1
                        else:
                            count -= 1
            cur_x = 0
        else:
            return None, None
        

# langtypes = { FOXDOT        : FoxDotInterpreter,
#               TIDAL         : TidalInterpreter,
#               TIDALSTACK    : StackTidalInterpreter,
#               SUPERCOLLIDER : SuperColliderInterpreter,
#               SONICPI       : SonicPiInterpreter,
#               DUMMY         : DummyInterpreter }


DEFAULT_INTERPRETERS  = { 
    0 : FoxDotInterpreter,
    1 : TidalInterpreter,
    2 : SuperColliderInterpreter
}