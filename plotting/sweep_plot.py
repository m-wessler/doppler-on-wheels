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
import os

# Available varids
#[u'VS1', u'DBZVC_F', u'VS1_F', u'DBZHC', u'ZDR', u'WIDTH', u'RHOHV', u'DBMVC_F', u'KDP_F', 
# u'WIDTH_F', u'ZDRM_F', u'ZDR_F', u'DBMHC', u'RHOHV_F', u'SNRHC_F', u'KDP', u'SNRHC', 
# u'DBMHC_F', u'PHIDP_F', u'DBZVC', u'VL1', u'NCP_F', u'VEL', u'SNRVC', u'PHIDP', u'NCP',
# u'VL1_F', u'ZDRM', u'DBMVC', u'SNRVC_F', u'DBZHC_F', u'VEL_F']

# # # USER ARGS # # #
iopdirs = ['iop1','iop5','iop6','iop7']
scriptvars = ['VEL']

zoom = 1.5 # 1 is normal (sweep fills frame)
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

def create_sweep(filename, figdir=None, subdir=None, varid=None, scale=zoom):
    #scale is zoom factor (2 is reasonable 1 is full out)

#    try:
    # read in the file, create a RadarMapDisplay object
    radar = pyart.io.read_cfradial(filename)
    print ("Read {}".format(filename))
    
    truck_lat = radar.latitude['data'][0]
    truck_lon = radar.longitude['data'][0]

    latmin = truck_lat - 0.45/scale
    latmax = truck_lat + 0.45/scale
    latint = .2/scale

    lonmin = truck_lon - 0.6/scale
    lonmax = truck_lon + 0.6/scale
    lonint = .3/scale

    z_ang = int(round(radar.fixed_angle['data'],0))
    
    # check if file exists do not overwrite or reproduce!
    _figpath = "{}/{}/{}/{}".format(figdir, subdir, varid, z_ang)
    figname = '_'.join(filename.split("/")[-1].split("_")[0:2])
    
    checkfile_png = _figpath + "/{}_{}_{}.png".format(varid, z_ang, figname)
    file_exists_png = os.path.isfile(checkfile_png)

    #checkfile_gif = _figpath + "/{}_{}_{}.gif".format(varid, z_ang, figname)
    #file_exists_gif = os.path.isfile(checkfile_png)

    if (file_exists_png):# or file_exists_gif):
        print("{} exists, skipping".format(checkfile_png))
        del radar

    else:
        # Change here if processing a single tilt or between two tilts, etc
        if z_ang >= 0:

            # rotate if not already rotated in radxconvert
            # truck_hdg_oftrue = 89.60 #from solar cal
            # radar.azimuth['data'] = (radar.azimuth['data'] + truck_hdg_oftrue) % 360.

            # Add specs for addl variables here
            if varid == 'DBZHC':
                cmapi = 'pyart_NWSRef'
                vmin = -5; vmax = 45

                gatefilter = pyart.correct.GateFilter(radar)
                gatefilter.exclude_below(varid, vmin)
                pyart.correct.despeckle.despeckle_field(radar, varid, gatefilter=gatefilter)

            elif varid == 'VEL':
                cmapi = 'pyart_NWSVel'
                vmin = -40; vmax = 40
                
                try:
                    gatefilter = pyart.correct.GateFilter(radar)
                    
                    # Gatefilter seems to need the DBZHC as a background reference frame
                    gatefilter.exclude_below('DBZHC', -5)
                    gatefilter.exclude_above('DBZHC', 45)

                    # Then filter the current variable
                    gatefilter.exclude_below(varid, vmin)
                    gatefilter.exclude_above(varid, vmax)
                    
                    pyart.correct.despeckle.despeckle_field(
                        radar, varid, threshold=(vmin,vmax), size=50, gatefilter=gatefilter)

                except:
                    pass
                
                #pyart unfolding routine

            else:
                # Allow pyart to choose default settings for given var
                cmapi = None
                vmin = None; vmax = None

            display = pyart.graph.RadarMapDisplay(radar)

            # plot note that 0 is the 'first' tilt due to the way that each tilt has own nc file
            display.plot_ppi_map(varid, 0, vmin=vmin, vmax=vmax, mask_outside=True, cmap=cmapi,
                                min_lon=lonmin, max_lon=lonmax, min_lat=latmin, max_lat=latmax,
                                lon_lines=np.arange(lonmin, lonmax, lonint), projection='lcc',
                                lat_lines=np.arange(latmin, latmax, latint), resolution='h',
                                lat_0=truck_lat, lon_0=truck_lon, gatefilter=gatefilter, embelish=True,
                                filter_transitions=False)

            # plot range rings at 10, 20, 30 and 40km
            #display.plot_range_ring(10., line_style='k--')
            #display.plot_range_ring(20., line_style='k--')
            #display.plot_range_ring(30., line_style='k--')
            #display.plot_range_ring(40., line_style='k--')
            #display.plot_range_ring(50., line_style='k--')

            # plots cross hairs
            #display.plot_line_xy(np.array([-50000.0, 50000.0]), np.array([0.0, 0.0]),
            #                    line_style='k-')
            #display.plot_line_xy(np.array([0.0, 0.0]), np.array([-50000.0, 50000.0]),
            #                    line_style='k-')

            # Indicate the radar location with a point (Or add other points....)
            #display.plot_point(radar.longitude['data'][0], radar.latitude['data'][0])

            _figpath = "{}/{}/{}/{}".format(figdir, subdir, varid, z_ang)
            mkdir_p(_figpath)
            figname = '_'.join(filename.split("/")[-1].split("_")[0:2])
            
            _figname = _figpath + "/{}_{}_{}.png".format(varid, z_ang, figname) #absolute!
            #_figname_gif = _figpath + "/{}_{}_{}.gif".format(varid, z_ang, figname) #absolute!

            plt.savefig(_figname, dpi=150)
            plt.close()

            # Convert to gif (!not working in multithreaded use!)
            #os.system('convert {} {}'.format(_figname, _figname_gif)) #png to gif inline
            #os.system('chmod 555 {}'.format(_figname_gif))
            #os.system('rm {}'.format(_figname))

            del radar
            del display
            del gatefilter
        
        else:
            del radar
            pass
    
    # except:
    #     with open(logpath,'a+') as wfp:
    #         wfp.write('{} {} failed, skipping\n'.format(filename, varid))

    return None

if __name__ == '__main__':

    for iopdir in iopdirs:
        ncpath = '/uufs/chpc.utah.edu/common/home/horel-group3/horel_data/mewessler/oreo/radar/'+iopdir+'/cfradial/'
        figpath = mkdir_p('/uufs/chpc.utah.edu/common/home/horel-group3/horel_data/mewessler/oreo/radar/'+iopdir+'/thumbs/')
        logpath = figpath + 'thumbs_log.txt'

        for scriptvar in scriptvars:

            with open(logpath,'a+') as wfp:
                wfp.write('------------------\n')
                wfp.write('Log Start: {}\n'.format(datetime.now().strftime('%Y/%m/%d %H:%M:%S')))
                wfp.write('------------------\n')

                subdirs = ['high/sur', 'high/sec', 'low/sur', 'low/sec']

                for Dir in subdirs:
                    try:
                        _flist = glob(ncpath+Dir+"/*.nc")
                        flist = [x for x in _flist if 'el-81.00_SUR' not in x]
                        print("\n\n# Of files: {} OK ?? (Press Enter to continue)".format(len(flist)))

                    except:
                        print("Dir {} not found".format(ncpath+Dir))
                    else:
                        if len(flist) > 0:
                            #singlethread
                            #for f in flist:
                            #    create_sweep(f, figdir=figpath, subdir=Dir, varid=scriptvar)

                            #multithread
                            cpunum = int(cpu_count())-1
                            p = Pool(cpunum)
                            wrapper = partial(create_sweep, figdir=figpath, subdir=Dir, varid=scriptvar)
                            p.map(wrapper, flist)
                            p.close()
                            p.join()