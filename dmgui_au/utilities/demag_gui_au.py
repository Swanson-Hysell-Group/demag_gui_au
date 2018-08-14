#!/usr/bin/env pythonw
# -*- coding: utf-8 -*-

import os
import sys
import warnings
# import pdb
import programs.demag_gui as dgl
from pmagpy.demag_gui_utilities import find_file
import programs.conversion_scripts2.cit_magic2 as cit_magic2
import programs.conversion_scripts.cit_magic as cit_magic3
from pmagpy import convert_2_magic as convert
from pmagpy.ipmag import combine_magic
from pmagpy.demag_gui_utilities import *
from numpy import array
from time import time, asctime
from threading import Thread
from wx import App, CallAfter, Timer, EVT_TIMER, ID_ANY
import wx
import wx.adv
from functools import reduce
import pmagpy.pmag as pmag
# get path names if set
try:
    import dmgui_au.config.user as user
    path_conf = user.demaggui_user
    data_dir = path_conf['data_dir']
    inp_dir = path_conf['inp_dir']
    data_output_path = path_conf['magic_out']
    pkg_dir = path_conf['pkg_dir']
    usr_configs_read = True
except:
    print("-W- Local paths used by this package have not been defined; please run the script setup.py")
    usr_configs_read = False

global CURRENT_VERSION
CURRENT_VERSION = pmag.get_version()

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Demag_GUIAU(dgl.Demag_GUI):

    def __init__(self, WD=None, write_to_log_file=True, inp_file=None,
                 delay_time=3, data_model=3, test_mode_on=True):
        global usr_configs_read, inp_dir, pkg_dir
        self.title = "Demag GUI Autoupdate | %s"%(CURRENT_VERSION.strip("pmagpy-"))
        if WD is None:
            self.WD = os.getcwd()
        else:
            self.WD = WD
        # self.delete_magic_files(self.WD)
        self.data_model = data_model
        self.delay_time = delay_time
        try:
            super().__init__(
                WD=WD,
                write_to_log_file=write_to_log_file,
                data_model=data_model,
                test_mode_on=test_mode_on
            )
        except ValueError:
            raise ValueError("Data model you entered is not a number")

        # make changes to the demag_gui parent frame
        # add buttons for triggering autoupdate functions
        self.au_add_buttons()
        # set AU icon
        self.au_set_icon()
        # add read .inp option to menubar
        self.menubar = super().GetMenuBar()
        menu_file = self.menubar.GetMenu(0)
        m_read_inp = menu_file.Insert(1, -1, "Read .inp file\tCtrl-I","")
        self.Bind(wx.EVT_MENU, self.on_menu_pick_read_inp, m_read_inp)
        self.menubar.Refresh()
        # make statusbar
        self.statusbar = self.CreateStatusBar(1)

        # find .inp file
        if inp_file is None:
            if usr_configs_read:
                inp_file_name = self.pick_inp(self,inp_dir)
            else:
                inp_file_name = self.pick_inp(self,self.WD)
        elif not os.path.isfile(inp_file):
            if os.path.isfile(os.path.join(self.WD, inp_file)):
                inp_file_name = os.path.join(self.WD, inp_file)
            elif usr_configs_read:
                if os.path.isfile(os.path.join(inp_dir, os.path.basename(inp_file))):
                    inp_file_name = os.path.join(inp_dir, os.path.basename(inp_file))
            else:
                print("-E- Could not find .inp file %s"%(inp_file))
                return
        else:
            inp_file_name = inp_file

        self.inp_file = inp_file_name
        magic_files = {}
        self.read_inp(self.WD, self.inp_file, magic_files, self.data_model)
        self.combine_magic_files(self.WD, magic_files, self.data_model)
        self.on_new_inp()
        self.update_loop(force_update=True)
        self.set_statusbar()

        self.timer = Timer(self, ID_ANY)
        self.timer.Start(self.delay_time*1000)
        self.Bind(EVT_TIMER, self.on_timer)

    ####################################################
    #  initialization methods/changes to the main GUI  #
    ####################################################

    def au_add_buttons(self):
        """
        add buttons to toggle timer and to stream from main data directory (Dropbox)
        """
        au_status_sizer = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.ID_ANY, "Autoupdate Status"), wx.VERTICAL)
        self.au_status_button = wx.ToggleButton(self.panel, id=wx.ID_ANY, size=(100*self.GUI_RESOLUTION, 25))
        self.au_status_button.SetValue(True)
        self.au_status_button.SetLabelMarkup("<span foreground='green'><b>{}</b></span>".format("Running"))
        self.go_live = wx.ToggleButton(self.panel, id=wx.ID_ANY, label='Go Live', size=(100*self.GUI_RESOLUTION, 25))
        au_status_btn_sizer = wx.GridSizer(2, 1, 10, 0)
        au_status_btn_sizer.AddMany([(self.au_status_button, 1, wx.ALIGN_RIGHT | wx.EXPAND),
                                    (self.go_live, 1, wx.ALIGN_RIGHT | wx.EXPAND)])
        au_status_sizer.Add(au_status_btn_sizer, 1, wx.TOP | wx.EXPAND, 5)
        self.top_bar_sizer.Add(au_status_sizer, 1, wx.ALIGN_LEFT |
                          wx.LEFT, self.top_bar_h_space)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.on_au_status_button, self.au_status_button)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.on_go_live, self.go_live)
        self.top_bar_sizer.Layout()

    def au_set_icon(self):
        """
        set icon
        """
        if usr_configs_read and sys.platform.startswith("darwin"):
            self.icon = wx.Icon()
            self.icon.LoadFile(
                    os.path.join(pkg_dir, "dmgui_au", "images",
                        "dmg_au_icon.icns"),
                    type=wx.BITMAP_TYPE_ICON, desiredWidth=1024,
                    desiredHeight=1024)
            self.taskicon = wx.adv.TaskBarIcon(wx.adv.TBI_DOCK)
            self.taskicon.SetIcon(self.icon)
            self.SetIcon(self.icon)
        elif usr_configs_read and sys.platform.startswith("win"):
            self.icon = wx.Icon()
            self.icon.LoadFile(
                    os.path.join(pkg_dir, "dmgui_au", "images",
                        "dmg_au_icon.ico"),
                    type=wx.BITMAP_TYPE_ICO, desiredWidth=1024,
                    desiredHeight=1024)
            self.SetIcon(self.icon)


    ####################
    #  static methods  #
    ####################

    @staticmethod
    def shortpath(abspath):
        return abspath.replace(os.path.expanduser('~') + os.sep, '~/', 1)

    @staticmethod
    def clr_output(raw_str):
        if str(raw_str).startswith('-I-'):
            print(bcolors.OKGREEN + raw_str + bcolors.ENDC)
        elif str(raw_str).startswith('-W-'):
            print(bcolors.WARNING + raw_str + bcolors.ENDC)
        elif str(raw_str).startswith('-E-'):
            print(bcolors.FAIL + raw_str + bcolors.ENDC)
        else:
            print(raw_str)

    ##############################################
    #  get attributes (and other useful values)  #
    ##############################################

    def get_inp(self):
        """
        get name of current inp file

        """
        return self.inp_file

    def get_status(self):
        try:
            timer_status = self.timer.IsRunning()
        except:
            timer_status = True
        return timer_status

    def get_status_msg(self):
        timer_status = self.get_status()
        if timer_status:
            return "Running"
        else:
            return "Paused"

    def get_sam_path(self):
        inp_file = open(self.inp_file, "r")
        lines = inp_file.read().splitlines()
        inp_file.close()
        all_sam_files = [
                self.shortpath(x.split('\t')[0]) for x in lines[2:]]
        if len(all_sam_files)==1:
            sam_files = os.path.dirname(all_sam_files[0])
        else:
            sam_files = os.path.commonpath(all_sam_files)
        return sam_files

    ########################################
    #  event handlers and related methods  #
    ########################################

    def toggle_timer(self):
        if self.timer.IsRunning():
            self.timer.Stop()
            print("-I- Timer stopped")
        else:
            self.timer.Start(self.delay_time*1000)
            print("-I- Timer started")
        self.set_statusbar()


    def set_statusbar(self):
        timer_status = self.get_status()
        if timer_status:
            self.statusbar.SetStatusText('Reading data from %s' % (self.get_sam_path()))
            self.statusbar.SetBackgroundColour(wx.Colour(193, 240, 193))
        else:
            self.statusbar.SetStatusText('Paused on data from %s' % (self.get_sam_path()))
            self.statusbar.SetBackgroundColour(wx.Colour(255, 255, 153))

    def on_menu_pick_read_inp(self, event):
        self.toggle_timer()
        global usr_configs_read, inp_dir
        if usr_configs_read:
            inp_file_name = self.pick_inp(self,inp_dir)
        else:
            inp_file_name = self.pick_inp(self,self.WD)
        if inp_file_name == None:
            self.toggle_timer()
            return
        self.inp_file = inp_file_name

        magic_files = {}
        self.read_inp(self.WD, self.inp_file, magic_files, self.data_model)
        self.combine_magic_files(self.WD, magic_files, self.data_model)

        # recall a bunch of methods from demag_gui __init__
        self.on_new_inp()
        self.update_loop(force_update=True)
        self.toggle_timer()
        return self.inp_file

    def on_timer(self, event):
        update_thread = Thread(target=self.update_loop, kwargs={
                               "inp_file": self.inp_file,
                               "delay_time": self.delay_time,
                               "data_model": self.data_model})
        update_thread.start()

    def on_au_status_button(self, event):
        self.toggle_timer()
        status, status_msg = self.get_status(), self.get_status_msg()
        if status:
            self.au_status_button.SetValue(True)
            self.au_status_button.SetLabelMarkup("<span foreground='green'><b>{}</b></span>".format(status_msg))
        else:
            self.au_status_button.SetValue(False)
            self.au_status_button.SetLabelMarkup("<span foreground='red'>{}</span>".format(status_msg))

    def on_go_live(self, event):
        if self.go_live.GetValue():
            self.au_status_button.Disable()
            self.go_live.SetLabelMarkup("<span foreground='green'><b>{}</b></span>".format("Live!"))
        else:
            self.au_status_button.Enable()
            self.go_live.SetLabel("Go Live")

    def on_new_inp(self):
        print("-I- Reading from .inp file %s"%(self.shortpath(self.inp_file)))
        inp = open(self.inp_file, "r")
        inp_lines = inp.read().splitlines()[2:]
        inp.close()
        for inp_line in inp_lines:
            print("-I- Tracking updates at %s" %
                  (self.shortpath(inp_line.split('\t')[0])))

        # initialize acceptence criteria with NULL values
        self.acceptance_criteria = self.read_criteria_file()

        # initalize starting variables and structures
        self.font_type = "Arial"
        if sys.platform.startswith("linux"):
            self.font_type = "Liberation Serif"

        self.preferences = self.get_preferences()
        self.dpi = 100

        self.all_fits_list = []

        self.pmag_results_data = {}
        for level in ['specimens', 'samples', 'sites', 'locations', 'study']:
            self.pmag_results_data[level] = {}

        self.high_level_means = {}
        for high_level in ['samples', 'sites', 'locations', 'study']:
            if high_level not in list(self.high_level_means.keys()):
                self.high_level_means[high_level] = {}

        self.ie_open = False
        self.check_orient_on = False
        self.list_bound_loc = 0
        self.all_fits_list = []
        self.current_fit = None
        self.selected_meas = []
        self.selected_meas_artists = []
        self.displayed_means = []
        self.selected_meas_called = False
        self.dirtypes = ['DA-DIR', 'DA-DIR-GEO', 'DA-DIR-TILT']
        self.bad_fits = []
        self.CART_rot, self.CART_rot_good, self.CART_rot_bad = array(
            []), array([]), array([])

        # initialize selecting criteria
        self.COORDINATE_SYSTEM = 'geographic'
        self.UPPER_LEVEL_SHOW = 'specimens'

        # Get data
        self.Data_info = self.get_data_info()  # Read  er_* data
        # Get data from magic_measurements and rmag_anistropy if exist.
        self.Data, self.Data_hierarchy = self.get_data()

        # get list of sites
        self.locations = list(self.Data_hierarchy['locations'].keys())
        self.locations.sort()  # get list of sites
        # get list of sites
        self.sites = list(self.Data_hierarchy['sites'].keys())
        self.sites.sort(key=spec_key_func)  # get list of sites
        self.samples = []  # sort the samples within each site
        for site in self.sites:
            self.samples.extend(
                sorted(self.Data_hierarchy['sites'][site]['samples'], key=spec_key_func))
        self.specimens = []  # sort the specimens within each sample
        for samp in self.samples:
            self.specimens.extend(
                sorted(self.Data_hierarchy['samples'][samp]['specimens'], key=spec_key_func))

        # first initialization of self.s only place besides init_cart_rot where it can be set without calling select_specimen
        if len(self.specimens) > 0:
            self.s = str(self.specimens[0])
        else:
            self.s = ""
        try:
            self.sample = self.Data_hierarchy['sample_of_specimen'][self.s]
        except KeyError:
            self.sample = ""
        try:
            self.site = self.Data_hierarchy['site_of_specimen'][self.s]
        except KeyError:
            self.site = ""

        # Draw figures and add text
        if self.Data and any(self.Data[s][k] if not isinstance(self.Data[s][k], type(array([]))) else self.Data[s][k].any() for s in self.Data for k in self.Data[s]):
            # get previous interpretations from pmag tables
            if self.data_model == 3.0 and 'specimens' in self.con.tables:
                self.get_interpretations3()
            else:
                self.update_pmag_tables()
            if not self.current_fit:
                self.update_selection_inp()
            else:
                self.Add_text()
                self.update_fit_boxes()
                self.update_high_level_stats()
        else:
            pass

    ####################################
    #  main methods for handling data  #
    ####################################

    def update_loop(self, inp_file=None, force_update=False, delay_time=1, data_model=3.0):
        print("-I- checking for updates at {0}".format(asctime()))
        if self.inp_file is None:
            inp_file_names = self.get_all_inp_files(self.WD)

            if inp_file_names == []:
                print("-W- No inp files found in any subdirectories of "
                      "%s, aborting update checking thread" % self.WD)
                self.timer.Stop()

                return
            magic_files = {}
            update_list = []

            for inp_file_name in inp_file_names:
                update_list.append(self.read_inp(
                    self.WD, inp_file_name, magic_files, data_model))
            update_needed = any(update_list)
        else:
            inp_file_name = self.inp_file
            magic_files = {}
            update_needed = self.read_inp(
                self.WD, inp_file_name, magic_files, data_model)
        if update_needed or force_update:
            self.reset_backend()

    def get_all_inp_files(self, WD=None):
        WD = os.path.abspath(WD)

        if not os.path.isdir(WD):
            print("-W- directory %s does not exist, aborting" % WD)

            return []
        try:
            all_inp_files = []

            for root, dirs, files in os.walk(WD):
                for d in dirs:
                    all_inp_files += self.get_all_inp_files(
                        os.path.join(root, d))

                for f in files:
                    if f.endswith(".inp") and f not in map(
                            lambda x: os.path.split(x)[1], all_inp_files):
                        all_inp_files.append(os.path.join(root, f))

            return all_inp_files
        except RuntimeError:
            raise RuntimeError(
                "Recursion depth exceded, please use different working "
                "directory. There are too many sub-directeries to walk")


    def read_inp(self, WD, inp_file_name, magic_files, data_model=3.0):
        inp_file = open(inp_file_name, "r")
        new_inp_file = ""

        if type(magic_files) != dict:
            magic_files = {}

        if 'measurements' not in magic_files.keys():
            magic_files['measurements'] = []

        if 'specimens' not in magic_files.keys():
            magic_files['specimens'] = []

        if 'samples' not in magic_files.keys():
            magic_files['samples'] = []

        if 'sites' not in magic_files.keys():
            magic_files['sites'] = []

        if 'locations' not in magic_files.keys():
            magic_files['locations'] = []

        lines = inp_file.read().splitlines()

        if len(lines) < 3:
            print("-W- File %s appears to be improperly formatted" %
                  (os.path.basename(inp_file_name)))
            return
        new_inp_file = lines[0] + "\r\n" + lines[1] + "\r\n"
        [lines.remove('') for i in range(lines.count(''))]

        format = lines[0].strip()
        header = lines[1].split('\t')
        update_files = lines[2:]
        update_data = False

        for i, update_file in enumerate(update_files):
            update_lines = update_file.split('\t')

            if not os.path.isfile(update_lines[0]):
                print("-I- %s not found; searching for location of file..." %
                      (update_lines[0]))
                sam_file_name = os.path.split(update_lines[0])[-1]
                new_file_path = find_file(sam_file_name, WD)

                if new_file_path is None or not os.path.isfile(new_file_path):
                    print("-W- %s does not exist in any subdirectory of %s and "
                          "will be skipped" % (update_lines[0], WD))
                    new_inp_file += update_file+"\r\n"

                    continue
                else:
                    print("-I- new location for file found at %s" %
                          (new_file_path))
                    update_lines[0] = new_file_path
            d = os.path.dirname(update_lines[0])
            name = os.path.basename(os.path.splitext(update_lines[0])[0])
            erspecf = name + "_specimens.txt"
            ersampf = name + "_samples.txt"
            ersitef = name + "_sites.txt"
            erlocf = name + "_locations.txt"
            f = name + ".magic"

            if os.path.join(d, f) in magic_files:
                new_inp_file += update_file+"\r\n"

                continue

            if float(update_lines[-1]) >= os.path.getmtime(update_lines[0]):
                no_changes = True
                # check specimen files for changes
                sam_file = open(update_lines[0])
                sam_file_lines = sam_file.read().splitlines()
                spec_file_paths = map(lambda x: os.path.join(
                    d, x.strip('\r \n')), sam_file_lines[2:])

                for spec_file_path in spec_file_paths:
                    if float(update_lines[-1]) < \
                            os.path.getmtime(spec_file_path):
                        no_changes = False

                        break

                if no_changes and os.path.isfile(os.path.join(WD, f)) \
                        and os.path.isfile(os.path.join(WD, erspecf)) \
                        and os.path.isfile(os.path.join(WD, ersampf)) \
                        and os.path.isfile(os.path.join(WD, ersitef)) \
                        and (data_model != 3.0 or
                             os.path.isfile(os.path.join(WD, erlocf))):
                    magic_files['measurements'].append(os.path.join(WD, f))
                    magic_files['specimens'].append(os.path.join(WD, erspecf))
                    magic_files['samples'].append(os.path.join(WD, ersampf))
                    magic_files['sites'].append(os.path.join(WD, ersitef))
                    magic_files['locations'].append(os.path.join(WD, erlocf))
                    new_inp_file += update_file+"\r\n"

                    continue

            if len(header) != len(update_lines):
                print("-W- length of header and length of entries for the file "
                      "%s are different and will be skipped" % (
                          update_lines[0]))
                new_inp_file += update_file+"\r\n"

                continue
            update_dict = {}

            for head, entry in zip(header, update_lines):
                update_dict[head] = entry

            if format == "CIT":
                CIT_kwargs = {}
                CIT_name = os.path.basename(
                    os.path.splitext(update_dict["sam_path"])[0])
                # cannot output to sam_path since this is in the locked
                # Dropbox directory; output to WD instead
                # CIT_kwargs["dir_path"] = reduce(lambda x,y: x+"/"+y,
                #   update_dict["sam_path"].split("/")[:-1])
                CIT_kwargs["dir_path"] = WD
                CIT_kwargs["user"] = ""
                CIT_kwargs["meas_file"] = CIT_name + ".magic"
                CIT_kwargs["spec_file"] = CIT_name + "_specimens.txt"
                CIT_kwargs["samp_file"] = CIT_name + "_samples.txt"
                CIT_kwargs["site_file"] = CIT_name + "_sites.txt"
                CIT_kwargs["loc_file"] = CIT_name + "_locations.txt"
                CIT_kwargs["locname"] = update_dict["location"]
                CIT_kwargs["methods"] = update_dict["field_magic_codes"]
                CIT_kwargs["specnum"] = update_dict["num_terminal_char"]
                CIT_kwargs["noave"] = update_dict[("dont_average_replicate"
                                                   "_measurements")]
                CIT_kwargs["samp_con"] = update_dict["naming_convention"]
                # CIT_kwargs["peak_AF"] = update_dict["peak_AF"]
                CIT_kwargs["magfile"] = os.path.basename(
                    update_dict["sam_path"])
                CIT_kwargs["input_dir_path"] = os.path.dirname(
                    update_dict["sam_path"])
                # CIT_kwargs["data_model"] = data_model

                if int(float(data_model)) == 3:
                    program_ran, error_message = convert.cit(**CIT_kwargs)
                else:
                    program_ran, error_message = cit_magic.main(
                        command_line=False, **CIT_kwargs)

                measp = os.path.join(
                    CIT_kwargs["dir_path"], CIT_kwargs["meas_file"])
                specp = os.path.join(
                    CIT_kwargs["dir_path"], CIT_kwargs["spec_file"])
                sampp = os.path.join(
                    CIT_kwargs["dir_path"], CIT_kwargs["samp_file"])
                sitep = os.path.join(
                    CIT_kwargs["dir_path"], CIT_kwargs["site_file"])
                locp = os.path.join(
                    CIT_kwargs["dir_path"], CIT_kwargs["loc_file"])
                # print(measp, specp, sampp, sitep, locp)

                if program_ran:
                    update_data = True
                    update_lines[-1] = time()
                    new_inp_file += reduce(lambda x, y: str(x) +
                                           "\t"+str(y), update_lines)+"\r\n"
                    magic_files['measurements'].append(measp)
                    magic_files['specimens'].append(specp)
                    magic_files['samples'].append(sampp)
                    magic_files['sites'].append(sitep)
                    magic_files['locations'].append(locp)
                else:
                    new_inp_file += update_file

                    if os.path.isfile(measp) and \
                       os.path.isfile(specp) and \
                       os.path.isfile(sampp) and \
                       os.path.isfile(sitep) and \
                       os.path.isfile(locp):
                        magic_files['measurements'].append(measp)
                        magic_files['specimens'].append(specp)
                        magic_files['samples'].append(sampp)
                        magic_files['sites'].append(sitep)
                        magic_files['locations'].append(locp)

        inp_file.close()
        out_file = open(inp_file_name, "w")
        out_file.write(new_inp_file)
        # out_file.close()

        return update_data

    def combine_magic_files(self, WD, magic_files, data_model=3.0):  # 2.5
        if type(magic_files) != dict:
            return

        if data_model == 3.0:
            if 'measurements' in magic_files.keys():
                combine_magic(magic_files['measurements'], os.path.join(
                    WD, "measurements.txt"))

            if 'specimens' in magic_files.keys():
                combine_magic(magic_files['specimens'],
                              os.path.join(WD, "specimens.txt"))

            if 'samples' in magic_files.keys():
                combine_magic(magic_files['samples'],
                              os.path.join(WD, "samples.txt"))

            if 'sites' in magic_files.keys():
                combine_magic(magic_files['sites'],
                              os.path.join(WD, "sites.txt"))

            if 'locations' in magic_files.keys():
                combine_magic(magic_files['locations'],
                              os.path.join(WD, "locations.txt"))
        else:
            if 'measurements' in magic_files.keys():
                combine_magic(magic_files['measurements'], os.path.join(
                    WD, "magic_measurements.txt"))

            if 'specimens' in magic_files.keys():
                combine_magic(magic_files['specimens'],
                              os.path.join(WD, "er_specimens.txt"))

            if 'samples' in magic_files.keys():
                combine_magic(magic_files['samples'],
                              os.path.join(WD, "er_samples.txt"))

            if 'sites' in magic_files.keys():
                combine_magic(magic_files['sites'],
                              os.path.join(WD, "er_sites.txt"))


    def delete_magic_files(self, WD, data_model=3.0):
        compiled_table_names = ['measurements', 'specimens', 'samples',
                            'sites', 'locations', 'contribution',
                            'criteria', 'ages', 'images']
        for mtable in compiled_table_names:
            if os.path.exists(os.path.join(WD,mtable+'.txt')):
                os.remove(os.path.join(WD,mtable+'.txt'))
                print("-I- Removing %s"%(os.path.join(WD,mtable+'.txt')))

    #############
    #  dialogs  #
    #############

    def pick_inp(self, parent, WD):
        dlg = wx.FileDialog(
            parent, message="Choose .inp file",
            defaultDir=WD,
            defaultFile="magic.inp",
            wildcard="*.inp",
            style=wx.FD_OPEN
        )

        if dlg.ShowModal() == wx.ID_OK:
            inp_file_name = dlg.GetPath()
        else:
            inp_file_name = None
        dlg.Destroy()

        return inp_file_name

    # TODO: The following method should be implemented in demag_gui; the call
    # to self.level_names.SetValue in self.update_selection is ignored because
    # the combobox self.level_names is readonly <08-12-18, Luke Fairchild> #

    def update_selection_inp(self):
        """
        Convenience function update display (figures, text boxes and
        statistics windows) with a new selection of specimen
        """
        self.clear_boxes()
        # commented out to allow propogation of higher level viewing state
        self.clear_high_level_pars()

        if self.UPPER_LEVEL_SHOW != "specimens":
            self.mean_type_box.SetValue("None")

        # --------------------------
        # check if the coordinate system in the window exists (if not change to "specimen" coordinate system)
        # --------------------------

        coordinate_system = self.coordinates_box.GetValue()
        if coordinate_system == 'tilt-corrected' and \
           len(self.Data[self.s]['zijdblock_tilt']) == 0:
            self.coordinates_box.SetStringSelection('specimen')
        elif coordinate_system == 'geographic' and \
                len(self.Data[self.s]['zijdblock_geo']) == 0:
            self.coordinates_box.SetStringSelection("specimen")
        if coordinate_system != self.coordinates_box.GetValue() and self.ie_open:
            self.ie.coordinates_box.SetStringSelection(
                self.coordinates_box.GetValue())
            self.ie.update_editor()
        coordinate_system = self.coordinates_box.GetValue()
        self.COORDINATE_SYSTEM = coordinate_system

        # --------------------------
        # update treatment list
        # --------------------------

        self.update_bounds_boxes()

        # --------------------------
        # update high level boxes
        # --------------------------

        high_level = self.level_box.GetValue()
        old_string = self.level_names.GetValue()
        new_string = old_string
        if high_level == 'sample':
            if self.s in self.Data_hierarchy['sample_of_specimen']:
                new_string = self.Data_hierarchy['sample_of_specimen'][self.s]
            else:
                new_string = ''
        if high_level == 'site':
            if self.s in self.Data_hierarchy['site_of_specimen']:
                new_string = self.Data_hierarchy['site_of_specimen'][self.s]
            else:
                new_string = ''
        if high_level == 'location':
            if self.s in self.Data_hierarchy['location_of_specimen']:
                new_string = self.Data_hierarchy['location_of_specimen'][self.s]
            else:
                new_string = ''
        self.level_names.SetString(0, new_string)
        if self.ie_open and new_string != old_string:
            self.ie.level_names.SetValue(new_string)
            self.ie.on_select_level_name(-1, True)

        # --------------------------
        # update PCA box
        # --------------------------

        self.update_PCA_box()

        # update warning
        self.generate_warning_text()
        self.update_warning_box()
        # update choices in the fit box
        self.update_fit_boxes()
        self.update_mean_fit_box()
        # measurements text box
        self.Add_text()
        # draw figures
        if self.current_fit:
            self.draw_figure(self.s, False)
        else:
            self.draw_figure(self.s, True)
        # update high level stats
        self.update_high_level_stats()
        # redraw interpretations
        self.update_GUI_with_new_interpretation()


def start(WD=None, inp_file=None, delay_time=1, vocal=False, data_model=3):
    global cit_magic

    if int(float(data_model)) == 3:
        cit_magic = cit_magic3
    else:
        cit_magic = cit_magic2
    app = App()
    dg = Demag_GUIAU(WD, not vocal, inp_file, delay_time, float(data_model))
    app.frame = dg
    app.frame.Center()
    app.frame.Show()
    app.MainLoop()

def main():
    kwargs = {}
    global data_output_path, usr_configs_read
    if usr_configs_read:
        kwargs['WD'] = data_output_path

    if "-WD" in sys.argv:
        wd_ind = sys.argv.index("-WD")
        kwargs['WD'] = sys.argv[wd_ind+1]

    if "-i" in sys.argv:
        inp_ind = sys.argv.index("-i")
        kwargs['inp_file'] = sys.argv[inp_ind+1]
    elif "--inp" in sys.argv:
        inp_ind = sys.argv.index("--inp")
        kwargs['inp_file'] = sys.argv[inp_ind+1]

    if "-d" in sys.argv:
        delay_ind = sys.argv.index("-d")
        kwargs['delay_time'] = float(sys.argv[delay_ind+1])
    elif "--delay" in sys.argv:
        delay_ind = sys.argv.index("--delay")
        kwargs['delay_time'] = float(sys.argv[delay_ind+1])

    if "-v" in sys.argv or "--vocal" in sys.argv:
        kwargs['vocal'] = True

    if "-dm" in sys.argv:
        dm_index = sys.argv.index("-dm")
        kwargs['data_model'] = sys.argv[dm_index+1]
    elif "--data_model" in sys.argv:
        dm_index = sys.argv.index("--data_model")
        kwargs['data_model'] = sys.argv[dm_index+1]
    start(**kwargs)

if __name__ == "__main__":
    main()
