# Author: Scott Collis (scollis@anl.gov)
# License: BSD 3 clause

# Modified & Expanded by: Michael Wessler (m.wessler@utah.edu)
# U of U Mountain Meteorology
# 1/2/2018

import numpy as np
import matplotlib.pyplot as plt
from glob import glob
import pyart
from multiprocessing import Pool, cpu_count
from functools import partial
from datetime import datetime
from netCDF4 import num2date
import os

# Available varids
#[u'VS1', u'DBZVC_F', u'VS1_F', u'DBZHC', u'ZDR', u'WIDTH', u'RHOHV', u'DBMVC_F', u'KDP_F', 
# u'WIDTH_F', u'ZDRM_F', u'ZDR_F', u'DBMHC', u'RHOHV_F', u'SNRHC_F', u'KDP', u'SNRHC', 
# u'DBMHC_F', u'PHIDP_F', u'DBZVC', u'VL1', u'NCP_F', u'VEL', u'SNRVC', u'PHIDP', u'NCP',
# u'VL1_F', u'ZDRM', u'DBMVC', u'SNRVC_F', u'DBZHC_F', u'VEL_F']

# # # USER ARGS # # #
iopdirs = ['iop7','iop6','iop5','iop1']
scriptvars = ['DBZHC_VEL']
# # # # # # # # # # #

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

def create_sweep(filename, figdir=None, subdir=None, varid=None, zoom=None):
    try:
        # read in the file, create a RadarMapDisplay object
        radar = pyart.io.read_cfradial(filename)
        print ("Read {}".format(filename))
        
        truck_lat = radar.latitude['data'][0]
        truck_lon = radar.longitude['data'][0]
        truck_alt = radar.altitude['data'][0]
        
        azimuth = radar.fixed_angle['data'][0]
        azimuth = int(round(azimuth,0))
        
        # check if file exists do not overwrite or reproduce!
        _figpath = "{}/{}/{}/{}".format(figdir, subdir, varid, azimuth)
        figname = '_'.join(filename.split("/")[-1].split("_")[0:2])
        
        checkfile_png = _figpath + "/{}_{}_{}.png".format(varid, azimuth, figname)
        file_exists_png = os.path.isfile(checkfile_png)

        #checkfile_gif = _figpath + "/{}_{}_{}.gif".format(varid, azimuth, figname)
        #file_exists_gif = os.path.isfile(checkfile_png)

        if (file_exists_png):# or file_exists_gif):
            print("{} exists, skipping".format(checkfile_png))
            del radar

        else:
            # rotate if not already rotated in radxconvert
            # truck_hdg_oftrue = 00.00 #from solar cal
            # radar.azimuth['data'] = (radar.azimuth['data'] + truck_hdg_oftrue) % 360.

            # Add specs for addl variables here
            if varid == 'DBZHC_VEL':
                varid1 = 'DBZHC'
                units1 = '[dBZ]'
                cmap1 = 'pyart_NWSRef'
                vmin1 = -5
                vmax1 = 50
                gf1 = pyart.correct.GateFilter(radar)
                gf1.exclude_below(varid1, vmin1)
                gf1.exclude_above(varid1, vmax1)
                pyart.correct.despeckle.despeckle_field(radar, varid1, gatefilter=gf1)

                fnyq = radar.get_nyquist_vel(0,True)
                _fnyq = int(np.ceil(fnyq / 10.0)) * 10

                varid2 = 'VEL'
                units2 = '[m/s]\nfnyq = {}'.format(round(fnyq,1))
                cmap2 = 'pyart_NWSVel'
                vmin2 = _fnyq * -1.
                vmax2 = _fnyq * 1.
                gf2 = pyart.correct.GateFilter(radar)
                gf2.exclude_below(varid1, vmin1)
                gf2.exclude_above(varid1, vmax1)
                gf2.exclude_below(varid2, vmin2)
                gf2.exclude_above(varid2, vmax2)
                pyart.correct.despeckle.despeckle_field(radar, varid2,
                    threshold=(vmin2,vmax2), size=35, gatefilter=gf2)

            else:
                print '{} Not Configured'.format(varid)

            display = pyart.graph.RadarMapDisplay(radar)

            # Prep plotting environment
            fig = plt.figure(figsize=[22, 12])
            ax1 = fig.add_subplot(211)
            
            time_start = num2date(radar.time['data'][0], radar.time['units'])
            time_text = ' ' + time_start.isoformat() + 'Z '
            
            title = 'RHI {} Azimuth {} \n Lat: {} Lon:{} Elevation:{}m'.format(
                time_text, azimuth, truck_lat, truck_lon, truck_alt)

            # Draw first plot
            p1 = display.plot(varid1, vmin=vmin1, vmax=vmax1, mask_outside=True, cmap=cmap1,
                            colorbar_flag=False, ax=ax1, title=title, gatefilter=gf1)

            cax1 = fig.add_axes([.9, .5365, 0.02, .364])
            colorbar_label = '{} {}'.format(varid1, units1)
            display.plot_colorbar(p1, cax=cax1, label=colorbar_label)

            #ax1.set_axisbelow(True)
            ax1.grid(linestyle='--', linewidth='0.25', color='k', alpha=0.5)
            
            # Draw second plot
            ax2 = fig.add_subplot(212)
            p2 = display.plot(varid2, vmin=vmin2, vmax=vmax2, mask_outside=True, cmap=cmap2,
                            colorbar_flag=False, ax=ax2, title='', gatefilter=gf2)

            cax2 = fig.add_axes([.9, .1, 0.02, .364])
            colorbar_label = '{} {}'.format(varid2, units2)
            display.plot_colorbar(p2, cax=cax2, label=colorbar_label)

            #ax2.set_axisbelow(True)
            ax2.grid(linestyle='--', linewidth='0.25', color='k', alpha=0.5)

            if zoom:
                x1 = ax1.get_xlim()
                y1 = ax1.get_ylim()
                ax1.set_xlim([x1[0], x1[1]/zoom[0]])
                ax1.set_ylim([y1[0], y1[1]/zoom[1]])

                x2 = ax2.get_xlim()
                y2 = ax2.get_ylim()
                ax2.set_xlim([x2[0], x2[1]/zoom[0]])
                ax2.set_ylim([y2[0], y2[1]/zoom[1]])

            _figpath = "{}/{}/{}/{}".format(figdir, subdir, varid, azimuth)
            mkdir_p(_figpath)
            figname = '_'.join(filename.split("/")[-1].split("_")[0:2])
            
            _figname = _figpath + "/{}_{}_{}.png".format(varid, azimuth, figname) #absolute!
            #_figname_gif = _figpath + "/{}_{}_{}.gif".format(varid, azimuth, figname) #absolute!

            plt.savefig(_figname, dpi=150)
            plt.close()

            # Convert to gif (!not working in multithreaded use!)
            #os.system('convert {} {}'.format(_figname, _figname_gif)) #png to gif inline
            #os.system('chmod 555 {}'.format(_figname_gif))
            #os.system('rm {}'.format(_figname))

            del radar
            del display
            del gf1; del gf2
    
    except:
        with open(logpath,'a+') as wfp:
            wfp.write('{} {} failed, skipping\n'.format(filename, varid))

    return None

if __name__ == '__main__':

    # Set None to shut off zoom, [x_factor, y_factor] otherwise
    zooms = {'iop1':[1,2], 'iop5':[1,2], 'iop6':None, 'iop7':[1,2]}

    for iopdir in iopdirs:
        ncpath = '/uufs/chpc.utah.edu/common/home/steenburgh-group7/OREO/'+iopdir+'/cfradial/'
        figpath = mkdir_p('/uufs/chpc.utah.edu/common/home/horel-group3/horel_data/mewessler/oreo/radar/'+iopdir+'/thumbs/')
        logpath = figpath + 'thumbs_log.txt'

        for scriptvar in scriptvars:

            with open(logpath,'a+') as wfp:
                wfp.write('------------------\n')
                wfp.write('Log Start: {}\n'.format(datetime.now().strftime('%Y/%m/%d %H:%M:%S')))
                wfp.write('------------------\n')

                subdirs = ['high/rhi', 'low/rhi']

                for Dir in subdirs:
                    try:
                        _flist = glob(ncpath+Dir+"/*.nc")
                        flist = [x for x in _flist if 'el-81.00_SUR' not in x]
                        print("\n\n# Of files: {} OK ?? (Press Enter to continue)".format(len(flist)))

                    except:
                        print("Dir {} not found".format(ncpath+Dir))
                    else:
                        if len(flist) > 0:
                            
                            #print ncpath+Dir, len(flist)
                            #for f in flist:
                            #    create_sweep(f, figdir=figpath, subdir=Dir, varid=scriptvar, zoom=zooms[iopdir])

                            #multithread
                            cpunum = int(cpu_count())-1
                            p = Pool(cpunum)
                            wrapper = partial(create_sweep, figdir=figpath, subdir=Dir, varid=scriptvar, zoom=zooms[iopdir])
                            p.map(wrapper, flist)
                            p.close()
                            p.join()