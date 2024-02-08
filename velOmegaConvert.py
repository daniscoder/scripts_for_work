#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

def main():
    pathIn = r'u:\zsolpatinskiy\surovyy2020\text_files\proc\036_Velocity_RMS_migr.txt'
    cmp_data_file = r'u:\zsolpatinskiy\surovyy2020\text_files\info\2190036_cmpinfo.txt'
    cmp_id = 1
    time_id = 4
    vel_id = 5
    txt_format = True

    if os.path.exists(pathIn):
        isfile = os.path.isfile(pathIn)
        if isfile:
            listfile = (os.path.split(pathIn)[1], )
            path = os.path.dirname(pathIn)
        else:
            listfile = sorted(os.listdir(pathIn))
            path = pathIn
        if txt_format:
            if os.path.exists(cmp_data_file):
                simvols = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}
                cmp_data = {}
                with open(cmp_data_file, 'r') as f:
                    for s in f:
                        ls = s.split()
                        if ls[0][0] in simvols:
                            cmp_data[ls[0]] = {
                                'Line': int(float(ls[1])),
                                'xLine': int(float(ls[2])),
                                'X': round(float(ls[3]), 1),
                                'Y': round(float(ls[4]), 1),
                                'Datcor': round(float(ls[5]))
                            }
                for filename in listfile:
                    curname = os.path.join(path, filename)
                    fname, fext = os.path.splitext(curname)
                    if isfile or (not fname.endswith('_omegaTxt') and fext == '.txt'):
                        outname = f'{fname}_omegaTxt{fext}'
                        with open(curname, 'r') as f, open(outname, 'w') as fnew:
                            cmp = col = None
                            for s in f:
                                ls = s.split()
                                if ls[cmp_id] in cmp_data:
                                    if ls[cmp_id] != cmp:
                                        if cmp:
                                            fnew.write('\n')
                                        cmp = ls[cmp_id]
                                        fnew.write('SPNT {:>10}{:>10}{:>10}{:>10}{:>10}\n'.format(cmp, cmp_data[cmp]['xLine'], cmp_data[cmp]['X'], cmp_data[cmp]['Y'], cmp_data[cmp]['Line']))
                                        fnew.write('VELF {:>10}{:>5}{:>5}{:>5}'.format(cmp, cmp_data[cmp]['Datcor'], round(float(ls[time_id])), round(float(ls[vel_id]))))
                                        col = 1
                                    else:
                                        if col < 5:
                                            fnew.write('{:>5}{:>5}'.format(round(float(ls[time_id])), round(float(ls[vel_id]))))
                                            col += 1
                                        else:
                                            fnew.write('\nVELF                {:>5}{:>5}'.format(round(float(ls[time_id])), round(float(ls[vel_id]))))
                                            col = 1
                        print(curname, '->', outname)
        else:
            for filename in listfile:
                curname = os.path.join(path, filename)
                fname, fext = os.path.splitext(curname)
                if isfile or (not fname.endswith('_omegaTab') and fext == '.txt'):
                    outname = f'{fname}_omegaTab{fext}'
                    with open(curname, 'r') as f, open(outname, 'w') as fnew:
                        cmp = None
                        for s in f:
                            ls = s.split()
                            if ls[cmp_id] != cmp:
                                cmp = ls[cmp_id]
                                fnew.write('{}\tNOT_USED\t{}\t{}\n'.format(cmp, ls[time_id], ls[vel_id]))
                            else:
                                fnew.write('\t\t{}\t{}\n'.format(ls[time_id], ls[vel_id]))
                    print(curname, '->', outname)
        print('Completed!')

if __name__ == '__main__':
    main()
