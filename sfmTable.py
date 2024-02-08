#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

def main():
    file_in = r'u:\santalovskiy\santalovskiy\text_files\CRS_MPFI\mpfi.txt'
    num = 9
    col = 0

    if os.path.isfile(file_in):
        fname, fext = os.path.splitext(file_in)

        data = []
        with open(file_in, 'r') as f:
            for s in f:
                data.append(s)

        i_first = num // 2
        i_last = num - i_first
        l = len(data)
        for i in range(l):
            punit = data[i].split()[col].replace("'", "")
            with open(f'{fname}_n{num}_{punit}{fext}', 'w') as fnew:
                for j in range(max(0, i - i_first), min(l, i + i_last)):
                    fnew.write(data[j])

        print('Completed!')

if __name__ == '__main__':
    main()
