# Author: Peter Veals (peter.veals@utah.edu)
# U of U Mountain Meteorology

# Modified & Expanded by: Michael Wessler (m.wessler@utah.edu)
# U of U Mountain Meteorology
# 1/4/2018 Final Version 1/8/2018

import os
from datetime import datetime, timedelta
from radx_config import config

def mkdir_p(mypath):
    '''Creates a directory. equivalent to using mkdir -p on the command line'''

    from errno import EEXIST
    from os import makedirs,path
 
    try:
        makedirs(mypath)
    except OSError as exc: # Python >2.5
        if exc.errno == EEXIST and path.isdir(mypath):
            pass
        else: raise

    return mypath

for iopnum in ['iop1','iop5','iop6','iop7']:

	start_date = config[iopnum]['start_date']
	end_date = config[iopnum]['end_date']
	in_date_subdir = config[iopnum]['in_date_subdir']

	indir = '/uufs/chpc.utah.edu/common/home/steenburgh-group7/OREO/'+iopnum+'/dorade/moments'
	dirs = ['high/rhi','high/sec','high/sur','low/rhi','low/sec','low/sur']

	outdir = mkdir_p(
		'/uufs/chpc.utah.edu/common/home/horel-group3/horel_data/mewessler/oreo/radarX/'+iopnum+'/cfradial')

	current_obj = datetime.strptime(start_date, '%Y%m%d')
	end_obj = datetime.strptime(end_date, '%Y%m%d')

	with open(outdir+'/'+iopnum+'_convert.log','w+') as log:

		log.write("-----------------\nBegin Convert {}\n".format(	
			datetime.now().strftime('%Y/%m/%d %H:%M:%S')))

		while current_obj<=end_obj:
			date=current_obj.strftime('%Y%m%d')
			Date=current_obj.strftime('%m%d')

			for Dir in dirs:

				if in_date_subdir:
					_indir = indir+'/'+Dir+'/'+date
				else:
					_indir = indir+'/'+Dir+'/'

				try:
					os.chdir(_indir)
					log.write("Changed Dir to {}\n".format(_indir))
				except:
					log.write("Could not access {}\n".format(_indir))
				else:
					mkdir_p(outdir+'/'+Dir)

					cmd_str = '/uufs/chpc.utah.edu/sys/pkg/radx/20140113/bin/RadxConvert '
					params_str = '-params /uufs/chpc.utah.edu/common/home/u1070830/oreo/code/radx/params/'+iopnum+'_params '
					arg_str = '' #'-print_params short' #For extra arguments not spec'ed in params file if desired
					out_str = '-f swp*'+Date+'* -outdir '+outdir+'/'+Dir

					try:
						os.system(cmd_str + params_str + arg_str + out_str)
						#print "\nin: {}\n".format(_indir)
						#print "out: {}\n".format(outdir+'/'+Dir)
						#print(cmd_str + params_str + arg_str + out_str)

					except:
						log.write("Failed to run RadxConvert\n")
					else:
						log.write("{} Success\n".format(Dir))

			current_obj += timedelta(days=1)

		log.write("Completed at {}\n------------------------\n".format(
			datetime.now().strftime('%Y/%m/%d %H:%M:%S')))
