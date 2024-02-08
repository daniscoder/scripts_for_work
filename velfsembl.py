#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np

def main():
    pathIn = r'u:\denisovskiy\3D\text_files\vel\17_01_Vrms_PSTM_fr_Vint_mod.txt'

    if os.path.exists(pathIn):
        isfile = os.path.isfile(pathIn)
        if isfile:
            listfile = (os.path.split(pathIn)[1], )
            path = os.path.dirname(pathIn)
        else:
            listfile = sorted(os.listdir(pathIn))
            path = pathIn
        for filename in listfile:
            curname = os.path.join(path, filename)
            fname, fext = os.path.splitext(curname)
            if isfile or (not fname.endswith('_sembl') and fext == '.txt'):
                simvols = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}
                outname = f'{fname}_sembl{fext}'
                with open(curname, 'r') as f, open(outname, 'w') as fnew:
                    cmp = None
                    vel = None
                    time = None
                    for s in f:
                        ls = s.split()
                        if ls[0][0] in simvols:
                            cmp_cur = int(ls[0])
                            if cmp_cur != cmp:
                                if vel:
                                    np_vel = np.array(vel)
                                    vel_sembl = np.arange(int(np.min(np_vel)), int(np.max(np_vel)), 1)
                                    vel_sembl = np.arange(1000, 8020, 20)
                                    time_sembl = np.interp(vel_sembl, np_vel, np.array(time))
                                    for i in range(len(vel_sembl)):
                                        fnew.write('{}\t{}\t{}\n'.format(cmp, vel_sembl[i], round(time_sembl[i], 0)))
                                cmp = cmp_cur
                                vel = [float(ls[6]), ]
                                time = [int(ls[5]), ]
                            else:
                                vel.append(float(ls[6]))
                                time.append(int(ls[5]))

                print(curname, '->', outname)
        print('Completed!')

if __name__ == '__main__':
    main()