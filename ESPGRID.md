# Building EspGrid from Source on Windows

[EspGrid](https://github.com/d0kt0r0/EspGrid) is a powerful tool for synchronising live coding environments over a network and was developed by David Ogborn. Configuration can be a bit tricky on Windows as it requires a few downloads so this is a quick run through of how to get installed and what might go wrong / how to fix it. This document outlines the necessary steps for building EspGrid from source on your own machine. Binaries are not always consistent across different versions of Windows so if you are having trouble with the executable downloaded from EspGrid's GitHub page, try and build from source. There are instructions available on that page but if you are newer to building executable files, then this is a more explicit, step-by-step guide to help you through.

# Instructions

## Step 1. Download & Install GNUStep Development Environment

You'll need to install this to have all of the libraries necessary to build executable files from source code. You can get the files by going to this web page:

[http://gnustep.org/windows/installer.html](http://gnustep.org/windows/installer.html)

Once you've opened the page, scroll down to "Download" and you'll see a table with some links. You will need to download the following packages. Do so by clicking on the release number in the appropriate row.

- GNUstep MSYS System
- GNUstep Core
- GNUstep Devel

Once you've downloaded them, double click to install and install in the suggested folder if possible (C:/GNUStep). You should add `C:/GNUStep/bin` to your system path too - see "Adding a directory to your system path" at the bottom of this document if you need to know how to do this.

## Step 2. Download the EspGrid repository in your GNUStep environment

What you've just installed is sort of like a mini Linux environment on your computer with all the tools needed to write and build programs. You can open the environment by going to `C:\GNUstep\msys\1.0` and running `msys.bat`. The files in this folder are the folders accessible from your GNUStep environment - so going to `home` will allow you to access your local environment files from the rest of Windows - this will be important to remember later.

Running `msys.bat` will open a terminal window. Type `pwd` and press Enter to see that the folder you are in is `home/<your_username>`. Clone the EspGrid GitHub repository by typing :

`git clone https://github.com/dktr0/EspGrid.git`

This will download all the necessary files onto your computer into a folder called `EspGrid`. You can see it has been downloaded by typing `ls` and pressing Enter.

## Step 3. Build the EspGrid program from source

'Go into' the newly downloaded EspGrid folder by typing `cd EspGrid` and press Enter. Type `ls` and press Enter to see the contents of the folder. You need to 'go into' the folder called EspGrid, so type `cd EspGrid` again and press enter. Now just type `make` and press Enter and you will build the program. The easiest way to access it from Winows explorer is to go to `C:/GNUStep/msys/1.0/home/<your_username>/EspGrid/EspGrid/` and find the file called `espgrid.exe`. Copy and paste this file to wherever it will be easy to access later. You can then run it just by double clicking it.

---

# Adding a directory to your system path

- Go to file explorer, right click on My Computer / This PC or similar and press "Properties"
- Go to "Advanced system settings" and click on the "Environment Variables" button near the  bottom
- There should be a variable called `PATH` and its value should have some directory names. Click on "Edit..." - if it is not there, create a new variable called `PATH`.
- On Windows 8 and earlier, add `C:/GNUStep/bin` to the variable value field but make sure you add a ; to the end of the last folder name.
- On Windows 10, click New and enter `C:/GNUStep/bin`
