# Demag GUI Autoupdate

A subclass of [PmagPy's DemagGUI](https://github.com/PmagPy/PmagPy) that tracks data files and
automatically updates changes. Other features that build upon this core functionality are in active
development. The bulk of this code was originally developed by [Kevin
Gaastra](https://github.com/Caoimhinmg) with small modifications over the years from other
contributors. This project is in active development.

The automated MagIC-format conversion built into DemagGUI AU currently only supports CIT-formatted
paleomagnetic data. Extending the application's compatibility to other formats should only be a
matter of automating other MagIC conversion scripts (already available in PmagPy for a wide array of
formats) in a similar way.

## Requirements

- [PmagPy](https://github.com/PmagPy/PmagPy)\
Instructions on how to download PmagPy can be found [here](https://github.com/PmagPy/PmagPy#how-to-get-it).

<!---
THE FOLLOWING APPLIES TO THE 'DEV' BRANCH ONLY!

> **Important:** Some features of DemagGUI AU that are in active development might rely on small tweaks to
> `demag_gui.py` that have not yet been integrated into PmagPy or are not included in the latest
> release. To ensure compatibility between this code and your installation of PmagPy, I would
> currently recommended downloading or cloning this fork of PmagPy:
> https://github.com/lfairchild/PmagPy/tree/au. More detailed instructions for how to go about this
> are provided down the page. (Ideally, this will only be necessary for the development branch of
> DemagGUI AU---the master branch should work on the latest PmagPy release.)


\
To download and use this fork (specifically the `au` branch), navigate to a directory of your choosing and enter the following on the command
line:
    ```
    git clone --single-branch -b au https://github.com/lfairchild/PmagPy.git
    ```
    This specific command should help to keep the installation as lightweight as possible by cloning
    only the `au` branch of the fork. If you prefer to simply download the forked repository or
    clone it normally via
    ```
    git clone https://github.com/lfairchild/PmagPy.git
    ``` 
    these methods should work equally well.
-->

## Installation and setup

Clone or fork this repository and download to your computer. 

Add the following lines to your `~/.profile` or `~/.bash_profile`
```bash
PATH=<path/to>/demag_gui_au:./:$PATH
PYTHONPATH=<path/to>/demag_gui_au:./:$PYTHONPATH
PATH=<path/to>/demag_gui_au/dmgui_au/utilities:./:$PATH
PYTHONPATH=<path/to>/demag_gui_au/dmgui_au/utilities:./:$PYTHONPATH
```
Navigate to the top directory `demag_gui_au` to run the setup script.
```bash
$ python setup.py
```
The program is interactive and will ask you to input the path to the main directory you would like
it to source data from. If this directory is located within your Dropbox folder (attn: UC Berkeley
pmag lab), run the script with the additional `dropbox` option. Unless you have a ginormous Dropbox
folder, this should narrow its search sufficiently such that no user input is necessary.
>For UC Berkeley folks, the script should automatically recognize the `Hargraves_Data` folder as the
top-level directory (if this is on your computer). 

```bash
$ python setup.py dropbox
```
Run `python setup.py -h` to see more options and documentation of the setup script.

Once it finds and confirms your primary data (source) directory, the script will write this and a
few other local path names to the configuration file `dmgui_au.conf` to be used by other programs in
the DemagGUI AU package. This configuration file is written in plain text and can be modified
at any time by opening it up in your favorite text editor.

The script will also create a new directory tree named `data` that is local to the package folder
and should not be moved. It will search for all `*.inp` files within the data directory and copy
them to the folder `data/inp_files/`.

If setup finishes successfully and you have configured your PATH correctly as outlined above, the
directory structure of the DemagGUI AU repository should now look something like this: 

```bash
demag_gui_au/
├── README.md
├── data/
│   └── inp_files/
├── dmgui_au/
│   ├── __init__.py
│   ├── dmgui_au.conf
│   ├── images/
│   ├── scripts/
│   └── utilities/
├── setup.log
└── setup.py
```

You should also now be able to begin running DemagGUI AU by entering `demag_gui_au.py` at the
command line. (Your current working directory should not matter, as the program should now be
configured to read and write only within the designated pathways specified during setup.) When the
GUI first launches, a pop-up dialog will prompt you to select one of the `*.inp` files copied during
the setup process.

## Other utilities
### Debugging inp files with `debug_inp.py`
----
The `debug_inp.py` module is a command line tool that allows for the identification and quick
correction of common errors within .inp files. 

Run the following on the command line to learn more:
```python
$ python debug_inp.py -h
```

### Combining inp files with `combine_inp_files.py`
----
The `combine_inp_files.py` module can be used to combine individual (typically site-level) inp files
into a higher-level grouping as specified by the user (e.g. location, stratigraphic section, study,
etc.). DemagGUI AU can then:

1. read these inp-file compilations
1. merge their data into a single MagIC contribution
1. update these files with new data in real time
1. and conveniently display all this data side by side --- allowing every new data point to be contextualized and compared within its respective data set
