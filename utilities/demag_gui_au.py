#!/usr/bin/env pythonw
# -*- coding: utf-8 -*-

import os
import sys
import programs.demag_gui as dgl
from pmagpy.demag_gui_utilities import find_file
import programs.conversion_scripts2.cit_magic2 as cit_magic2
import programs.conversion_scripts.cit_magic as cit_magic3
from pmagpy.ipmag import combine_magic
from time import time, asctime
from threading import Thread
from wx import App, CallAfter, Timer, EVT_TIMER, ID_ANY
import wx
from functools import reduce
import pmagpy.pmag as pmag
import pdb
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
        self.delete_magic_files(self.WD)
        self.data_model = data_model
        self.inp_file = inp_file
        magic_files = {}
        self.read_inp(self.WD, self.inp_file, magic_files, self.data_model)
        self.combine_magic_files(self.WD, magic_files, self.data_model)
        self.delay_time = delay_time
        try:
            super(Demag_GUIAU, self).__init__(
                WD=WD,
                write_to_log_file=write_to_log_file,
                data_model=data_model,
                test_mode_on=test_mode_on
            )
        except ValueError:
            raise ValueError("Data model you entered is not a number")
        self.menubar = super(Demag_GUIAU, self).GetMenuBar()
        menu_file = self.menubar.GetMenu(0)
        m_read_inp = menu_file.Append(-1, "Read .inp file\tCtrl-I","")
        self.Bind(wx.EVT_MENU, self.on_menu_pick_read_inp, m_read_inp)
        self.menubar.Refresh()

        self.timer = Timer(self, ID_ANY)
        self.timer.Start(delay_time*1000)
        self.Bind(EVT_TIMER, self.on_timer)

    def on_timer(self, event):
        update_thread = Thread(target=self.update_loop, kwargs={
                               "inp_file": self.inp_file,
                               "delay_time": self.delay_time,
                               "data_model": self.data_model})
        update_thread.start()

    def update_loop(self, inp_file=None, delay_time=1, data_model=3.0):
        print("checking for updates at {0}".format(asctime()))

        if inp_file is None:
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
            inp_file_name = inp_file
            magic_files = {}
            update_needed = self.read_inp(
                self.WD, inp_file_name, magic_files, data_model)

        if update_needed:
            print("resetting...")
            self.combine_magic_files(
                self.WD, magic_files, data_model=data_model)
            CallAfter(self.reset_backend, warn_user=False, reset_interps=False)
            # CallAfter(super().recalculate_current_specimen_interpreatations)
            print("reset")

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
            print(".inp file improperly formated")

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
                CIT_kwargs["peak_AF"] = update_dict["peak_AF"]
                CIT_kwargs["magfile"] = os.path.basename(
                    update_dict["sam_path"])
                CIT_kwargs["input_dir_path"] = os.path.dirname(
                    update_dict["sam_path"])
                CIT_kwargs["data_model"] = data_model

                if int(float(data_model)) == 3:
                    program_ran, error_message = cit_magic.convert(
                        **CIT_kwargs)
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
                print(measp, specp, sampp, sitep, locp)

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
        inp_file_name = self.pick_inp(self,self.WD)
        if inp_file_name == None: return
        self.inp_file = inp_file_name

        self.delete_magic_files(self.WD)
        super().clear_high_level_pars()
        super().clear_boxes()
        super().clear_interpretations()
        magic_files = {}
        self.read_inp(self.WD, self.inp_file, magic_files, self.data_model)
        # print(magic_files)
        self.combine_magic_files(self.WD, magic_files, self.data_model)
        pdb.set_trace()
        super().reset_backend(warn_user=False, reset_interps=False)
        # self.reset_backend(warn_user=False, reset_interps=False)
        # self.calculate_high_levels_data()
        # self.update_selection()
        # self.recalculate_current_specimen_interpreatations()
        # self.reset_backend(warn_user=False, reset_interps=False)

        self.timer = Timer(self, ID_ANY)
        self.timer.Start(self.delay_time*1000)
        self.Bind(EVT_TIMER, self.on_timer)
        # self.update_high_level_stats()

"""
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
