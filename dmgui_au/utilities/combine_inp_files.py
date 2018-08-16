import os,sys
# import programs.demag_gui as dgl
import utilities.demag_gui_au as dgl
from wx import App

def combine_inp(sd, out_path='.'):
    """
    Function that combines inp files into a single inp file which allows faster running of autoupdate wrapper of demag_gui.

    @param: sd - top level directory whose subdirectories and files will be searched for  all inp files to combine.
    """

    sd = os.path.abspath(sd)

    if out_path is None:
        out_path = sd
    else:
        out_path = os.path.abspath(out_path)

    app = App()
    dg = dgl.Demag_GUIAU(WD=sd,write_to_log_file=False)
    all_inp_files = dg.get_all_inp_files(WD=sd)
    if all_inp_files == []: print("No inp files found, aborting process"); return

    ofs = ""
    ofs += "CIT\r\n"
    ofs += "sam_path\tfield_magic_codes\tlocation\tnaming_convention\tnum_terminal_char\tdont_average_replicate_measurements\tpeak_AF\ttime_stamp\r\n"
    for inpfn in all_inp_files:
        if 'all.inp' in inpfn: continue
        inpf = open(inpfn, 'r')
        lines = inpf.read().splitlines()
        for line in lines[2:]:
            ofs += line+'\r\n'

    print('Writing file - ' + out_path + 'all' + '.inp')
    of = open(out_path + 'all' + '.inp', 'w+')
    of.write(ofs)
    of.close()

    magic_files = []
    dg.read_inp(out_path + 'all' + '.inp',magic_files)
    print('Writing file - ' + out_path + 'magic_measurements.txt')
    dg.combine_magic_files(magic_files)

if __name__=="__main__":
    if "-h" in sys.argv: help(combine_inp); sys.exit()
    try: sd = sys.argv[1]
    except IndexError:
        print("no directory to search for inp files to combine, aborting")
        sys.exit()
    try:
        out_path = sys.argv[2]
        combine_inp(sd, out_path=out_path)
    except:
        combine_inp(sd)
