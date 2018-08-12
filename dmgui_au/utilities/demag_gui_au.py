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
from functools import reduce
import pmagpy.pmag as pmag
try: # get path names if set
    import dmgui_au.config.user as user
    path_conf = user.demaggui_user
    data_dir = path_conf['data_dir']
    inp_dir = path_conf['inp_dir']
    data_output_path = path_conf['magic_out']
    usr_configs_read = True
except:
    warnings.warn("Local paths used by this package have not been defined; please run the script setup.py")
    usr_configs_read = False

global CURRENT_VERSION
CURRENT_VERSION = pmag.get_version()


class Demag_GUIAU(dgl.Demag_GUI):

    def __init__(self, WD=None, write_to_log_file=True, inp_file=None,
                 delay_time=3, data_model=3, test_mode_on=True):
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

        global usr_configs_read, inp_dir
        if usr_configs_read and inp_file is None:
            inp_file_name = self.pick_inp(self,inp_dir)
        elif inp_file is None:
            inp_file_name = self.pick_inp(self,self.WD)
        else:
            inp_file_name = inp_file
        self.inp_file = inp_file_name
        magic_files = {}
        self.read_inp(self.WD, self.inp_file, magic_files, self.data_model)
        self.combine_magic_files(self.WD, magic_files, self.data_model)
        self.on_new_inp()
        self.update_loop(force_update=True)

        # self.high_level_type, self.high_level_name, self.dirtype = super().get_levels_and_coordinates_names()
        self.menubar = super().GetMenuBar()
        menu_file = self.menubar.GetMenu(0)
        m_read_inp = menu_file.Prepend(-1, "Read .inp file\tCtrl-I","")
        self.Bind(wx.EVT_MENU, self.on_menu_pick_read_inp, m_read_inp)
        self.menubar.Refresh()

        self.timer = Timer(self, ID_ANY)
        self.timer.Start(delay_time*1000)
        self.Bind(EVT_TIMER, self.on_timer)

    def get_inp(self):
        """
        get name of current inp file

        Returns
        -------
        self.inp_file

        """
        return self.inp_file

    @staticmethod
    def shortpath(abspath):
        return abspath.replace(os.path.expanduser('~') + os.sep, '~/', 1)

    def on_timer(self, event):
        update_thread = Thread(target=self.update_loop, kwargs={
                               "inp_file": self.inp_file,
                               "delay_time": self.delay_time,
                               "data_model": self.data_model})
        update_thread.start()

    def update_loop(self, inp_file=None, force_update=False, delay_time=1, data_model=3.0):
        print("checking for updates at {0}".format(asctime()))

        if self.inp_file is None:
            inp_file_names = self.get_all_inp_files(self.WD)

            if inp_file_names == []:
                print("No inp files found in any subdirectories of "
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
            disableAll = wx.WindowDisabler()
            wait = wx.BusyInfo('Compiling required data, please wait...')
            wx.SafeYield()
            # self.combine_magic_files(
            #     self.WD, magic_files, data_model=data_model)
            self.reset_backend()
            del wait

    def get_all_inp_files(self, WD=None):
        WD = os.path.abspath(WD)

        if not os.path.isdir(WD):
            print("directory %s does not exist, aborting" % WD)

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
            print("File %s appears to be improperly formatted" %
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
                print("%s not found searching for location of file" %
                      (update_lines[0]))
                sam_file_name = os.path.split(update_lines[0])[-1]
                new_file_path = find_file(sam_file_name, WD)

                if new_file_path is None or not os.path.isfile(new_file_path):
                    print("%s does not exist in any subdirectory of %s and "
                          "will be skipped" % (update_lines[0], WD))
                    new_inp_file += update_file+"\r\n"

                    continue
                else:
                    print("new location for file found at %s" %
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
                print("length of header and length of enteries for the file "
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
                print("Removing %s"%(os.path.join(WD,mtable+'.txt')))

    def pick_inp(self, parent, WD):
        dlg = wx.FileDialog(
            parent, message="choose .inp file",
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

    def on_menu_pick_read_inp(self, event):
        self.timer.Stop()
        global usr_configs_read, inp_dir
        if usr_configs_read:
            inp_file_name = self.pick_inp(self,inp_dir)
        else:
            inp_file_name = self.pick_inp(self,self.WD)
        if inp_file_name == None: return
        self.inp_file = inp_file_name

        magic_files = {}
        self.read_inp(self.WD, self.inp_file, magic_files, self.data_model)
        self.combine_magic_files(self.WD, magic_files, self.data_model)

        # recall a bunch of methods from demag_gui __init__
        self.on_new_inp()
        self.update_loop(force_update=True)
        # self.reset_backend()
        self.timer.Start(self.delay_time*1000)
        return self.inp_file

    def on_new_inp(self):
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

# TODO: This should be implemented in demag_gui; the call to
# self.level_names.SetValue in self.update_selection is ignored because
# the combobox self.level_names is readonly <12-08-18, Luke Fairchild> #

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




"""
        # super(Demag_GUIAU, self).all_fits_list = []

        super(Demag_GUIAU, self).pmag_results_data = {}
        for level in ['specimens', 'samples', 'sites', 'locations', 'study']:
            super(Demag_GUIAU, self).pmag_results_data[level] = {}

        super(Demag_GUIAU, self).high_level_means = {}
        for high_level in ['samples', 'sites', 'locations', 'study']:
            if high_level not in list(super(Demag_GUIAU, self).high_level_means.keys()):
                super(Demag_GUIAU, self).high_level_means[high_level] = {}

        super(Demag_GUIAU, self).ie_open = False
        super(Demag_GUIAU, self).check_orient_on = False
        super(Demag_GUIAU, self).list_bound_loc = 0
        super(Demag_GUIAU, self).color_dict = {}
        super(Demag_GUIAU, self).colors = ['#4ED740', '#9840D7', '#FFBD4C',
                       '#398AAD', '#E96640', "#CB1A9F", "55C2B6", "FFD44C"]
        for name, hexval in matplotlib.colors.cnames.items():
            if name == 'black' or name == 'blue' or name == 'red':
                continue
            elif name == 'green' or name == 'yellow' or name == 'maroon' or name == 'cyan':
                super(Demag_GUIAU, self).color_dict[name] = hexval
            else:
                super(Demag_GUIAU, self).color_dict[name] = hexval
                super(Demag_GUIAU, self).colors.append(hexval)
        super(Demag_GUIAU, self).all_fits_list = []
        super(Demag_GUIAU, self).current_fit = None
        super(Demag_GUIAU, self).selected_meas = []
        super(Demag_GUIAU, self).selected_meas_artists = []
        super(Demag_GUIAU, self).displayed_means = []
        super(Demag_GUIAU, self).selected_meas_called = False
        super(Demag_GUIAU, self).dirtypes = ['DA-DIR', 'DA-DIR-GEO', 'DA-DIR-TILT']
        super(Demag_GUIAU, self).bad_fits = []
        super(Demag_GUIAU, self).CART_rot, super(Demag_GUIAU, self).CART_rot_good, super(Demag_GUIAU, self).CART_rot_bad = array(
            []), array([]), array([])

        # initialize selecting criteria
        super(Demag_GUIAU, self).COORDINATE_SYSTEM = 'geographic'
        super(Demag_GUIAU, self).UPPER_LEVEL_SHOW = 'specimens'

        # Get data
        super(Demag_GUIAU, self).Data_info = super(Demag_GUIAU, self).get_data_info()  # Read  er_* data
        # Get data from magic_measurements and rmag_anistropy if exist.
        super(Demag_GUIAU, self).Data, super(Demag_GUIAU, self).Data_hierarchy = super(Demag_GUIAU, self).get_data()

        # get list of sites
        super(Demag_GUIAU, self).locations = list(super(Demag_GUIAU, self).Data_hierarchy['locations'].keys())
        super(Demag_GUIAU, self).locations.sort()  # get list of sites
        # get list of sites
        super(Demag_GUIAU, self).sites = list(super(Demag_GUIAU, self).Data_hierarchy['sites'].keys())
        super(Demag_GUIAU, self).sites.sort(key=spec_key_func)  # get list of sites
        super(Demag_GUIAU, self).samples = []  # sort the samples within each site
        for site in super(Demag_GUIAU, self).sites:
            super(Demag_GUIAU, self).samples.extend(
                sorted(super(Demag_GUIAU, self).Data_hierarchy['sites'][site]['samples'], key=spec_key_func))
        super(Demag_GUIAU, self).specimens = []  # sort the specimens within each sample
        for samp in super(Demag_GUIAU, self).samples:
            super(Demag_GUIAU, self).specimens.extend(
                sorted(super(Demag_GUIAU, self).Data_hierarchy['samples'][samp]['specimens'], key=spec_key_func))

        # first initialization of self.s only place besides init_cart_rot where it can be set without calling select_specimen
        if len(super(Demag_GUIAU, self).specimens) > 0:
            super(Demag_GUIAU, self).s = str(super(Demag_GUIAU, self).specimens[0])
        else:
            super(Demag_GUIAU, self).s = ""
        try:
            super(Demag_GUIAU, self).sample = super(Demag_GUIAU, self).Data_hierarchy['sample_of_specimen'][super(Demag_GUIAU, self).s]
        except KeyError:
            super(Demag_GUIAU, self).sample = ""
        try:
            super(Demag_GUIAU, self).site = super(Demag_GUIAU, self).Data_hierarchy['site_of_specimen'][super(Demag_GUIAU, self).s]
        except KeyError:
            super(Demag_GUIAU, self).site = ""

        # self.scrolled_panel = wx.lib.scrolledpanel.ScrolledPanel(
        #     self, wx.ID_ANY)  # make the Panel
        # self.panel = wx.Panel(self, wx.ID_ANY)
        # self.side_panel = wx.Panel(self, wx.ID_ANY)
        # self.init_UI()  # build the main frame
        # self.create_menu()  # create manu bar
        # self.scrolled_panel.SetAutoLayout(True)
        # self.scrolled_panel.SetupScrolling()  # endable scrolling

        # Draw figures and add text
        if super(Demag_GUIAU, self).Data and any(super(Demag_GUIAU, self).Data[s][k] if not isinstance(super(Demag_GUIAU, self).Data[s][k], type(array([]))) else super(Demag_GUIAU, self).Data[s][k].any() for s in super(Demag_GUIAU, self).Data for k in super(Demag_GUIAU, self).Data[s]):
            # get previous interpretations from pmag tables
            if super(Demag_GUIAU, self).data_model == 3.0 and 'specimens' in super(Demag_GUIAU, self).con.tables:
                super(Demag_GUIAU, self).get_interpretations3()
            else:
                super(Demag_GUIAU, self).update_pmag_tables()
            if not super(Demag_GUIAU, self).current_fit:
                super(Demag_GUIAU, self).update_selection()
            else:
                super(Demag_GUIAU, self).Add_text()
                super(Demag_GUIAU, self).update_fit_boxes()
                super(Demag_GUIAU, self).update_high_level_stats()
        else:
            pass


#         self.delete_magic_files(self.WD)
#         self.update_loop(force_update=True)

#         # magic_files = {}
#         # self.read_inp(self.WD, self.inp_file, magic_files, self.data_model)
#         # self.combine_magic_files(self.WD, magic_files, self.data_model)

#         super().clear_high_level_pars()
#         super().clear_boxes()
#         super().clear_interpretations()

#         super().all_fits_list = []

#         super().pmag_results_data = {}
#         for level in ['specimens', 'samples', 'sites', 'locations', 'study']:
#             super().pmag_results_data[level] = {}

#         super().high_level_means = {}
#         for high_level in ['samples', 'sites', 'locations', 'study']:
#             if high_level not in list(self.high_level_means.keys()):
#                 super().high_level_means[high_level] = {}

#         # magic_files = {}
#         # self.read_inp(self.WD, self.inp_file, magic_files, self.data_model)
#         # print(magic_files)
#         # self.combine_magic_files(self.WD, magic_files, self.data_model)
#         # pdb.set_trace()
#         # super().reset_backend(warn_user=False, reset_interps=False)
#         # self.reset_backend(warn_user=False, reset_interps=False)
#         # self.calculate_high_levels_data()
#         # self.update_selection()
#         # self.recalculate_current_specimen_interpreatations()
#         # self.reset_backend(warn_user=False, reset_interps=False)

#         # self.timer = Timer(self, ID_ANY)
#         # self.timer.Start(self.delay_time*1000)
#         # self.Bind(EVT_TIMER, self.on_timer)
#         # self.update_high_level_stats()


update_GUI_with_new_interpretation



        mb = self.GetMenuBar()
        am = mb.GetMenu(2)

        self.menubar = wx.MenuBar()

        #-----------------
        # File Menu
        #-----------------

        menu_file = wx.Menu()


        m_change_WD = menu_file.Append(-1, "Change Working Directory\tCtrl-W","")
        self.Bind(wx.EVT_MENU, self.on_menu_change_working_directory, m_change_WD)


        #self.menubar.Append(menu_preferences, "& Preferences")
        self.menubar.Append(menu_file, "&File")
        self.menubar.Append(menu_edit, "&Edit")
        self.menubar.Append(menu_Analysis, "&Analysis")
        self.menubar.Append(menu_Tools, "&Tools")
        self.menubar.Append(menu_Help, "&Help")
        #self.menubar.Append(menu_Plot, "&Plot")
        #self.menubar.Append(menu_results_table, "&Table")
        #self.menubar.Append(menu_MagIC, "&MagIC")
        self.SetMenuBar(self.menubar)
"""


'''
some old code from original __init__:

    self.update_loop(inp_file=inp_file,delay_time=0,data_model=data_model)

    update_needed = self.read_inp(self.WD,inp_file_name,magic_files,data_model)
    ry:
        super(Demag_GUIAU, self).__init__(WD=WD,
            write_to_log_file=write_to_log_file,data_model=data_model,
            test_mode_on=test_mode_on)

    except ValueError: raise ValueError("Data model you entered is not a "
        "number")

    if not os.path.isdir(os.path.join(os.getcwd(),'data')):
        os.makedirs('data')
    self.WD=os.path.join(os.getcwd(),'data')
'''


def start(WD=None, inp_file=None, delay_time=1, vocal=False, data_model=3):
    global cit_magic

    if int(float(data_model)) == 3:
        cit_magic = cit_magic3
    else:
        cit_magic = cit_magic2
    app = App()
    dg = Demag_GUIAU(WD, not vocal, inp_file, delay_time, float(data_model))
    # dg = Demag_GUIAU(None, vocal, inp_file, delay_time, float(data_model))
    app.frame = dg
    app.frame.Center()
    app.frame.Show()
    app.MainLoop()


def main():
    kwargs = {}
    global data_dir, inp_dir, data_output_path, usr_configs_read
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
