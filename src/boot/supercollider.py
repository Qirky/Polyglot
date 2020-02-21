import os.path

def get_startup_file(foxdot=False, tidal=False):
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "boot.scd")
    with open(path, "w") as f:
        if foxdot:
            f.write("FoxDot.start;\n")
        if tidal:
            f.write("SuperDirt.start;\n")
        f.write("Troop.start;")
    return path

def find_path():
    """ Finds the sclang executalbe and returns the path """

    import platform, os

    OS = platform.system()

    if(OS == "Windows"):

        sclangloc = os.popen('where /R "C:\\Program Files" sclang.exe').read()

        sclangloc = sclangloc.split("\n")[0] # in case there are multiple

    elif(OS == "Linux"):

        sclangloc = "sclang"

    else: # Mac?
        print("Operating system unrecognised")
        #Potentially get the user to choose their OS from a list?
        #Then run the corresponding functions
        
        sclangloc = None

    return sclangloc
