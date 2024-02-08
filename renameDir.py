#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os


def main():
    patchName = r'/gpfs/omega/wgdisk/taymur/sgy'

    if os.path.exists(patchName):
        for fname in sorted(os.listdir(patchName)):
            fcur = '{}/{}'.format(patchName, fname)
            fcurRoot, fcurExt = os.path.splitext(fcur)
            if fcurExt == '.txt':
                fnew = fcur.replace('_mod', '')
                os.rename(fcur, fnew)

if __name__ == '__main__':
    main()
