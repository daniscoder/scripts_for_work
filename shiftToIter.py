#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from statistics import mean

def main():
    fname1 = r'/ud/zsolpatinskiy/surovyy2020/sfm_tables/xpert/2191033_reflMiser7_shift1.txt'
    shifts = (80, 60, 40, 10)

    if os.path.exists(fname1):
        fname, fext = os.path.splitext(fname1)
        f = open(fname1, 'r')
        data = []
        for s in f:
            ls = s.split()
            if len(ls) > 0:
                data.append(ls)

        for i, shift in enumerate(shifts):
            fnew = open('{}{}{}'.format(fname[:-1], i + 1, fext), 'w')
            for ls in data:
                fnew.write('{}\t{}\t{}\t{}\n'.format(ls[0], ls[1], ls[2], min(shift, int(ls[3]))))
            fnew.close()
        f.close()

        print('Completed')
    else:
        print('Error')

if __name__ == '__main__':
    main()

