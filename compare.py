#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

def main():
    filename1 = r'/mp/home/danis/Downloads/Zap-Bykovskaja.x'
    filename2 = r'/mp/home/danis/Downloads/Zap-Bykovskaja_red.x'

    if os.path.exists(filename1) and os.path.exists(filename2):
        f1 = open(filename1, 'r')
        f2 = open(filename2, 'r')
        fname, fext = os.path.splitext(filename1)
        fnew = open('{}_{}{}'.format(fname, 'diff', fext), 'w')
        sf2 = set()
        for s in f2:
            sf2.add(s)
        for i, s in enumerate(f1):
            if not s in sf2:
                fnew.write(s)

        fnew.close()
        f1.close()
        f2.close()


if __name__ == '__main__':
    main()
