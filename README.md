# Demag GUI Autoupdate

A subclass of [PmagPy's DemagGUI](https://github.com/PmagPy/PmagPy) that tracks data files and automatically updates changes. Other features that build upon this core functionality are in active development. The bulk of this code was originally developed by [Kevin Gaastra](https://github.com/Caoimhinmg) with small modifications over the years from other contributors.

## Requirements

- [PmagPy](https://github.com/PmagPy/PmagPy)\
Instructions on how to download PmagPy can be found [here](https://github.com/PmagPy/PmagPy#how-to-get-it).\
\
*Some features of DemagGUI AU that are in active development might rely on small tweaks to `demag_gui.py`
that have not yet been integrated into PmagPy or are not included in the latest release. To ensure
compatibility between this code and your installation of PmagPy, **it is recommended that you download
or clone this fork of PmagPy**: https://github.com/lfairchild/PmagPy/tree/au.
(Ideally, this will only be necessary for the development branch of DemagGUI AU---the master branch should work on the
latest PmagPy release.)*\
\
To download and use this fork (specifically the `au` branch), navigate to a directory of your choosing and enter the following on the command
line:
    ```git
    git clone --single-branch -b au https://github.com/lfairchild/PmagPy.git
    ```
    This should

## Installation and setup

Clone or fork this repository and download to your computer. 

Add the following lines to your `~/.profile` or `~/.bash_profile`
```
PATH=<path/to>/demag_gui_au:./:$PATH
PYTHONPATH=<path/to>/demag_gui_au:./:$PYTHONPATH
PATH=<path/to>/demag_gui_au/dmgui_au/utilities:./:$PATH
PYTHONPATH=<path/to>/demag_gui_au/dmgui_au/utilities:./:$PYTHONPATH
```
Navigate to the top directory `demag_gui_au` to run the setup script.
```python
python setup.py
```
If your main data directory is located within your Dropbox folder (attn: UC Berkeley lab), run the script
with the additional `dropbox` option:
```python
python setup.py dropbox
```
For more options, run:
```python
python setup.py -h
```

The setup script will create a new directory tree named `data`. It will search for all `*.inp` files
within the data directory and copy them to the folder `data/inp_files/`. 

If setup finishes successfully, you should now be able to enter `demag_gui_au.py` at the command
line. A pop-up dialog will prompt you to select one of the `*.inp` files for the program to read.

## Other utilities
### Debugging .inp files
See `dmgui_au/utilities/debug_inp.py`

### Combining .inp files
See `dmgui_au/utilities/combine_inp.py`

