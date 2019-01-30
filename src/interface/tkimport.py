try:
    import Tkinter as Tk
    import tkFileDialog
    import tkFont
    import tkMessageBox
    from tkColorChooser import askcolor as tkAskColor
except ImportError:
    import tkinter as Tk
    from tkinter import filedialog as tkFileDialog
    from tkinter import messagebox as tkMessageBox
    from tkinter import font as tkFont
    from tkinter.colorchooser import askcolor as tkAskColor