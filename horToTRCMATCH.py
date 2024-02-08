#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

def main():
    filename = r'/ud/zsolpatinskiy/surovyy2020/text_files/hor_vel5inva/0820010_hor_forSCVA_vel6.txt'
    taperUp = 50
    taperDn = 50

    if os.path.exists(filename):
        fname, fext = os.path.splitext(filename)
        f = open(filename, 'r')
        fnew = open('{}_{}{}'.format(fname, 'trcmatch', fext), 'w')
        tabline1 = '{}\tPLUS\t{}\t1\t0\tCOMPUTED\tCOMPUTED\n'
        tabline2 = '\t\t{}\t0\t1\tCOMPUTED\tCOMPUTED\n'
        for s in f:
            ls = s.split()
            fnew.write(tabline1.format(ls[0], int(ls[2]) - taperUp))
            fnew.write(tabline2.format(int(ls[2]) + taperDn))
        fnew.close()
        f.close()

        print('Completed')
    else:
        print('Error')
        print('Файл {} не найден'.format(filename))


if __name__ == '__main__':
    main()
