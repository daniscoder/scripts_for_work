#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os


def main():
    offs_var_txt = r'C:\pycharm\pythonProject\crs_off.txt'
    file_in = r'u:\santalovskiy\santalovskiy\text_files\CRS_MPFI\mpfi.txt'
    off_min = 25
    off_dif = 50

    if os.path.isfile(file_in) and os.path.isfile(offs_var_txt):
        fname, fext = os.path.splitext(file_in)

        data = []
        with open(file_in, 'r') as f:
            for s in f:
                data.append(s)

        offs_var = []
        with open(offs_var_txt, 'r') as f:
            for s in f:
                offs_var.append([float(i) for i in s.split()])

        for off_i, offs in enumerate(offs_var):
            i_min = int((offs[0] - off_min) / off_dif + 0.5)
            i_max = int((offs[1] - off_min) / off_dif - 0.5) + 1
            p_unit = '{:>03}'.format(off_i + 1)
            with open(f'{fname}_{p_unit}{fext}', 'w') as fnew:
                for i in range(i_min, i_max + 1):
                    fnew.write(data[i])

        print('Completed!')


if __name__ == '__main__':
    main()
