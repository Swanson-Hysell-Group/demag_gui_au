import os,sys
import programs.demag_gui as dgl
from pmagpy.demag_gui_utilities import find_file
import programs.cit_magic3 as cit_magic
from pmagpy.ipmag import combine_magic
from time import time
from threading import Thread
from wx import App, CallAfter, Timer, EVT_TIMER, ID_ANY

class Demag_GUIAU(dgl.Demag_GUI):

    def __init__(self,WD=None, write_to_log_file=True, inp_file=None, delay_time=3, data_model=2.5):
        super(Demag_GUIAU, self).__init__(WD=WD,write_to_log_file=write_to_log_file)
        self.timer = Timer(self, ID_ANY)
        self.timer.Start(delay_time*1000)
        self.Bind(EVT_TIMER, self.on_timer)

    def on_timer(self,event):
        update_thread = Thread(target = self.update_loop,kwargs={"inp_file": inp_file, "delay_time": delay_time, "data_model": data_model})
        update_thread.start()

    def update_loop(self,inp_file=None,delay_time=1,data_model=2.5):
        print("checking for updates")
        if inp_file == None:
            inp_file_names = self.get_all_inp_files(self.WD)
            if inp_file_names == []:
                print("No inp files found in any subdirectories of %s, aborting update checking thread"%self.WD); return
            magic_files = {}
            update_list = []
            for inp_file_name in inp_file_names:
                update_list.append(self.read_inp(self.WD,inp_file_name,magic_files,data_model))
            update_needed = any(update_list)
        else:
            inp_file_name = inp_file
            magic_files = {}
            update_needed = self.read_inp(self.WD,inp_file_name,magic_files,data_model)

        if update_needed:
            print("reseting")
            self.combine_magic_files(self.WD,magic_files,data_model)
            CallAfter(self.reset_backend,warn_user=False,reset_interps=False)
            print("reset")

    def get_all_inp_files(self, WD=None):
        if not os.path.isdir(WD): print("directory %s does not exist, aborting"%WD); return []
        try:
            all_inp_files = []
            for root, dirs, files in os.walk(WD):
                for d in dirs:
                    all_inp_files += self.get_all_inp_files(d)
                for f in files:
                    if f.endswith(".inp"):
                         all_inp_files.append(os.path.join(root, f))
            return all_inp_files
        except RuntimeError:
            raise RuntimeError("Recursion depth exceded, please use different working directory there are too many sub-directeries to walk")

    def read_inp(self, WD,inp_file_name,magic_files,data_model=2.5):
        inp_file = open(inp_file_name, "r")
        new_inp_file = ""

        if type(magic_files) != dict: magic_files = {}
        if 'measurements' not in magic_files.keys(): magic_files['measurements']=[]
        if 'specimens' not in magic_files.keys(): magic_files['specimens']=[]
        if 'samples' not in magic_files.keys(): magic_files['samples']=[]
        if 'sites' not in magic_files.keys(): magic_files['sites']=[]
        if 'locations' not in magic_files.keys(): magic_files['locations']=[]

        lines = inp_file.read().splitlines()
        if len(lines) < 3: print(".inp file improperly formated"); return
        new_inp_file = lines[0] + "\r\n" + lines[1] + "\r\n"
        [lines.remove('') for i in range(lines.count(''))]
        format = lines[0].strip()
        header = lines[1].split('\t')
        update_files = lines[2:]
        update_data = False
        for i,update_file in enumerate(update_files):
            update_lines = update_file.split('\t')
            if not os.path.isfile(update_lines[0]):
                print("%s not found searching for location of file"%(update_lines[0]))
                sam_file_name = os.path.split(update_lines[0])[-1]
                new_file_path = find_file(sam_file_name, WD)
                if new_file_path == None or not os.path.isfile(new_file_path):
                    print("%s does not exist in any subdirectory of %s and will be skipped"%(update_lines[0], WD))
                    new_inp_file += update_file+"\r\n"
                    continue
                else:
                    print("new location for file found at %s"%(new_file_path))
                    update_lines[0] = new_file_path
            d = os.path.dirname(update_lines[0])
            name = os.path.basename(os.path.splitext(update_lines[0])[0])
            erspecf = name + "_er_specimens.txt"
            ersampf = name + "_er_samples.txt"
            ersitef = name + "_er_sites.txt"
            erlocf = name + "_locations.txt"
            f = name + ".magic"
            if os.path.join(d,f) in magic_files:
                new_inp_file += update_file+"\r\n"
                continue
            if float(update_lines[-1]) >= os.path.getmtime(update_lines[0]):
                no_changes = True
                #check specimen files for changes
                sam_file = open(update_lines[0])
                sam_file_lines = sam_file.read().splitlines()
                spec_file_paths = map(lambda x: os.path.join(d,x.strip('\r \n')), sam_file_lines[2:])
                for spec_file_path in spec_file_paths:
                    if float(update_lines[-1]) < os.path.getmtime(spec_file_path):
                        no_changes=False; break
                if no_changes and os.path.isfile(os.path.join(WD,f)) \
                              and os.path.isfile(os.path.join(WD,erspecf)) \
                              and os.path.isfile(os.path.join(WD,ersampf)) \
                              and os.path.isfile(os.path.join(WD,ersitef)) \
                              and (data_model != 3.0 or os.path.isfile(os.path.join(WD,erlocf))):
                    magic_files['measurements'].append(os.path.join(WD,f))
                    magic_files['specimens'].append(os.path.join(WD,erspecf))
                    magic_files['samples'].append(os.path.join(WD,ersampf))
                    magic_files['sites'].append(os.path.join(WD,ersitef))
                    magic_files['locations'].append(os.path.join(WD,erlocf))
                    new_inp_file += update_file+"\r\n"
                    continue
            if len(header) != len(update_lines):
                print("length of header and length of enteries for the file %s are different and will be skipped"%(update_lines[0]))
                new_inp_file += update_file+"\r\n"
                continue
            update_dict = {}
            for head,entry in zip(header,update_lines):
                update_dict[head] = entry
            if format == "CIT":
                CIT_kwargs = {}
                CIT_name = os.path.basename(os.path.splitext(update_dict["sam_path"])[0])

                CIT_kwargs["dir_path"] = WD #reduce(lambda x,y: x+"/"+y, update_dict["sam_path"].split("/")[:-1])
                CIT_kwargs["user"] = ""
                CIT_kwargs["meas_file"] = CIT_name + ".magic"
                CIT_kwargs["spec_file"] = CIT_name + "_er_specimens.txt"
                CIT_kwargs["samp_file"] = CIT_name + "_er_samples.txt"
                CIT_kwargs["site_file"] = CIT_name + "_er_sites.txt"
                CIT_kwargs["loc_file"] = CIT_name + "_locations.txt"
                CIT_kwargs["locname"] = update_dict["location"]
                CIT_kwargs["methods"] = update_dict["field_magic_codes"]
                CIT_kwargs["specnum"] = update_dict["num_terminal_char"]
                CIT_kwargs["avg"] = update_dict["dont_average_replicate_measurements"]
                CIT_kwargs["samp_con"] = update_dict["naming_convention"]
                CIT_kwargs["peak_AF"] = update_dict["peak_AF"]
                CIT_kwargs["magfile"] = os.path.basename(update_dict["sam_path"])
                CIT_kwargs["input_dir_path"] = os.path.dirname(update_dict["sam_path"])
                CIT_kwargs["data_model"] = data_model

                program_ran, error_message = cit_magic.main(command_line=False, **CIT_kwargs)

                measp = os.path.join(CIT_kwargs["dir_path"],CIT_kwargs["meas_file"])
                specp = os.path.join(CIT_kwargs["dir_path"],CIT_kwargs["spec_file"])
                sampp = os.path.join(CIT_kwargs["dir_path"],CIT_kwargs["samp_file"])
                sitep = os.path.join(CIT_kwargs["dir_path"],CIT_kwargs["site_file"])
                locp = os.path.join(CIT_kwargs["dir_path"],CIT_kwargs["loc_file"])

                if program_ran:
                    update_data = True
                    update_lines[-1] = time()
                    new_inp_file += reduce(lambda x,y: str(x)+"\t"+str(y), update_lines)+"\r\n"
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
        return update_data

    def combine_magic_files(self, WD,magic_files,data_model=2.5):
        if type(magic_files) != dict: return
        if data_model==3.0:
            if 'measurements' in magic_files.keys():
                combine_magic(magic_files['measurements'], os.path.join(WD,"measurements.txt"))
            if 'specimens' in magic_files.keys():
                combine_magic(magic_files['specimens'], os.path.join(WD,"specimens.txt"))
            if 'samples' in magic_files.keys():
                combine_magic(magic_files['samples'], os.path.join(WD,"samples.txt"))
            if 'sites' in magic_files.keys():
                combine_magic(magic_files['sites'], os.path.join(WD,"sites.txt"))
            if 'locations' in magic_files.keys():
                combine_magic(magic_files['locations'], os.path.join(WD,"locations.txt"))
        else:
            if 'measurements' in magic_files.keys():
                combine_magic(magic_files['measurements'], os.path.join(WD,"magic_measurements.txt"))
            if 'specimens' in magic_files.keys():
                combine_magic(magic_files['specimens'], os.path.join(WD,"er_specimens.txt"))
            if 'samples' in magic_files.keys():
                combine_magic(magic_files['samples'], os.path.join(WD,"er_samples.txt"))
            if 'sites' in magic_files.keys():
                combine_magic(magic_files['sites'], os.path.join(WD,"er_sites.txt"))

    def pick_inp(self,parent,WD):
        dlg = wx.FileDialog(
            parent, message="choose .inp file",
            defaultDir=WD,
            defaultFile="magic.inp",
            wildcard="*.inp",
            style=wx.OPEN
            )
        if dlg.ShowModal() == wx.ID_OK:
            inp_file_name = dlg.GetPath()
        else:
            inp_file_name = None
        dlg.Destroy()
        return inp_file_name

if __name__=="__main__":

    inp_file = None
    if "-i" in sys.argv:
        inp_ind = sys.argv.index("-i")
        inp_file = sys.argv[inp_ind+1]
    elif "--inp" in sys.argv:
        inp_ind = sys.argv.index("--inp")
        inp_file = sys.argv[inp_ind+1]
    delay_time = 1
    if "-d" in sys.argv:
        delay_ind = sys.argv.index("-d")
        delay_time = float(sys.argv[delay_ind+1])
    elif "--delay" in sys.argv:
        delay_ind = sys.argv.index("--delay")
        delay_time = float(sys.argv[delay_ind+1])
    vocal = False
    if "-v" in sys.argv or "--vocal" in sys.argv:
        vocal = True
    data_model = 2.5
    if "-dm" in sys.argv:
        dm_index = sys.argv.index("-dm")
        data_model = sys.argv[dm_index+1]
    elif "--data_model" in sys.argv:
        dm_index = sys.argv.index("--data_model")
        data_model = sys.argv[dm_index+1]

    app = App()
    dg = Demag_GUIAU(None, not vocal, inp_file, delay_time, data_model)
    app.frame = dg
    app.frame.Center()
    app.frame.Show()
    app.MainLoop()
