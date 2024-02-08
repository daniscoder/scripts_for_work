#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import numpy as np


def main():
    path_in = Path(r"E:\Processing\Hamakarskiy\vel4_rms_ham_marhyan_161306.txt").absolute()
    vel_inc = 20
    vel_max = 8000

    numbers = set('0123456789')
    vel: list
    time: list

    def vel_interp():
        vel[0] = np.polyval(np.polyfit(time[0:2], vel[0:2], 1), 0)
        time[0] = 0
        time.append(time[-1] + (time[-1] - time[-2]))
        vel.append(np.polyval(np.polyfit(time[-3:-1], vel[-2:], 1), time[-1]))
        vel_semblance = np.arange(vel_inc * (vel[0] // vel_inc), vel_max + vel_inc, vel_inc)
        time_semblance = np.interp(vel_semblance, np.array(vel), np.array(time))
        vel_semblance[0] = np.polyval(np.polyfit(time_semblance[0:2], vel_semblance[0:2], 1), 0)
        time_semblance[0] = 0
        for j in range(len(vel_semblance)):
            out.write('{}\t{}\t{}\n'.format(cmp, round(float(vel_semblance[j])), round(float(time_semblance[j]))))

    if path_in.exists():
        for file in (path_in, ) if path_in.is_file() else sorted(list(file for file in path_in.glob('*' if path_in.is_dir() else path_in.stem) if not file.stem.endswith('semblance'))):
            with open(str(file), 'r') as f, open(str(Path(file.parent) / f'{file.stem}_semblance{file.suffix}'), 'w') as out:
                cmp = None
                vel = []
                time = []
                for s in f:
                    ls = s.split()
                    if ls:
                        if ls[0][0] in numbers:
                            time.append(int(ls[0]))
                            vel.append(float(ls[1]))
                        else:
                            for i in range(0, len(ls), 2):
                                if ls[i] == 'CMP':
                                    if len(vel) > 1:
                                        vel_interp()
                                        vel = []
                                        time = []
                                    cmp = int(ls[i + 1])
                if len(vel) > 1:
                    vel_interp()

        print('Completed!')


if __name__ == '__main__':
    main()
