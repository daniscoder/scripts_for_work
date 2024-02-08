#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from statistics import mean

def main():
    fnames = (
        r'/ud/taymur/648511/sfm_tables/02/512738_02_R_11.txt',
        r'/ud/taymur/648511/sfm_tables/02/512738_02_R_12.txt',
    )
    p_i = 1
    s_i = 2

    if os.path.exists(fnames[0]):
        fname, fext = os.path.splitext(fnames[0])
        data = {}
        for f in (open(fname, 'r') for fname in fnames):
            for s in f:
                ls = s.split()
                if len(ls) > 0:
                    point = int(ls[p_i])
                    if not point in data:
                        data[point] = [float(ls[s_i])]
                    else:
                        data[point].append(float(ls[s_i]))
        for p in data:
            data[p] = mean(data[p])

        fnew = open('{}_{}{}'.format(fname, 'horm', fext), 'w')
        buff = ''
        for i in range(min(p_i, s_i)):
            buff += '{:<12}'.format(i)
        for p in sorted(data.keys()):
            fnew.write('{}{}{:>12}\n'.format(buff, p, round(data[p], 4)))
        fnew.close()
        f.close()

        print('Completed')
    else:
        print('Error')

if __name__ == '__main__':
    main()

