#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

def main():
    filename = r'/ud/taymur/648511/sfm_tables/09/512738_09_V.txt'

    if os.path.exists(filename):
        fname, fext = os.path.splitext(filename)
        f = open(filename, 'r')
        fnew = open('{}_{}{}'.format(fname, 'gen', fext), 'w')
        cmp = None
        for s in f:
            ls = s.split()
            if ls[2] != cmp:
                cmp = ls[2]
                fnew.write('{}\tNOT_USED\t{}\t{}\n'.format(cmp, ls[3], ls[4]))
            else:
                fnew.write('\t\t{}\t{}\n'.format(ls[3], ls[4]))
        fnew.close()
        f.close()
        print('Completed')

if __name__ == '__main__':
    main()
