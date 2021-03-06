# PolyGlot

## Multi-lingual collaborative live coding

*Polyglot (adjective): knowing or using several languages.*

PolyGlot is a user interface that is designed to allow users to collaborate closely regardless of what languages they know. It also allows users that are skilled across multiple programming languages to utilise their different strengths simultaneously and showcase their multi-lingual virtuosity.

Currently, PolyGlot only allows users to to work with [FoxDot](https://github.com/Qirky/FoxDot), [TidalCycles](https://tidalcycles.org/), and [SuperCollider](http://supercollider.github.io/) but hopefully in the future this number will increase. To synchronise the audio, PolyGlot also requires the [EspGrid](https://github.com/dktr0/EspGrid) tool to be running on your computer. 

## Setting up

### 1. Install the necessary live coding environments

Generating music using multiple live coding languages at once can put quite a strain on your CPU so ideally you should have one member of your ensemble 'hosting' a different language for your jam. So far, PolyGlot can talk to FoxDot, TidalCycles, and SuperCollider (which is required for the first two). Installation instructions can be found via the links below:

- [SuperCollider](http://supercollider.github.io/)
- [FoxDot](https://github.com/Qirky/FoxDot)
- [TidalCycles](https://tidalcycles.org/)

Make sure you've installed your required languages and be sure to test they're working correctly before proceeding.

### 2. Download and run EspGrid

To synchronise the musical events across different live coding environments, PolyGlot relies on the languages being able to interface with the open source synchronisation tool, EspGrid. Installation is usually straightforward but may vary depending on your  operating system so be sure follow instructions carefully. Usually this is just downloading and double-clicking an executable, but instructions for building from source can be found on the page's github. EspGrid will automatically find other instances of EspGrid on your network and co-ordinate tempo and timing, so no further configuration should be required. Only those running a live coding language during a PolyGlot session will require EspGrid to be running on their system.

- [EspGrid GitHub page](https://github.com/dktr0/EspGrid)

### 3. Install necessary SuperCollider Quarks

If you have installed FoxDot and/or TidalCycles you will have encountered "Quarks" for SuperCollider, which are external libraries for the language. Any users who wish  to use SuperCollider as the host language will need to install the "Troop" quark and the "EspGrid" quark using the following code:

    Quarks.install("http://github.com/Qirky/TroopQuark.git");
    Quarks.install("https://github.com/d0kt0r0/Esp.sc.git");

Simply copy and paste it into the SuperCollider window, highlight both lines and press `Ctrl+Enter`.

### 4. Setting up for playing

The diagram below outlines how a typical PolyGlot session might look like:

![PolyGlot Architecture](images/arch.png)

One user (or a separate machine) is running the server application (see "Running the Server" for more information on doing this) and every user is running the client, which is connected to the server. Each user is hosting a different language except one, which is hosting none. All users are co-located and can hear the audio output from any users hosting a language. EspGrid is running on the network, which each language is communicating with to synchronise audio. All users can use the client to execute code on the machine hosting the corresponding language.

**IMPORTANT** 

- Make sure you start EspGrid *before* PolyGlot. EspGrid seems to works best in clock mode 2, which FoxDot will set it to automatically. If you are not using FoxDot then you will need to start EspGrid with a `-clockMode 2` flag.
- Make sure you run `Troop.start` / `FoxDot.start` in SuperCollider before opening PolyGlot if you are using SuperCollider or FoxDot as the host language.

## Running PolyGlot

PolyGlot requires Python (2 or 3) to be installed on your system, which can be downloaded here: [https://www.python.org/](https://www.python.org/).

### Running the Server

One user needs to be running the server application. This can be done using the command `python run-server.py`, which will prompt the user for a password. Type the password you want (can be left blank) and press return. The console should now display the IP address of the machine and information about users joining / leaving the session.

### Running the Client

To open the client, run `python run-client.py`, which will open a login window that will require the IP address and port number (as seen on the server application window) a user name and the server's password. It also has a set of tick boxes for "active languages": these are the languages you will be hosting on your machine. So if you are only running FoxDot, untick TidalCycles and SuperCollider and press OK to log in.

You will then be greeted with an interface with three text boxes; one for each language. Type code and press `Ctrl+Enter` to run!
