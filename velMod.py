#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os


def main():
    patchName = r'/gpfs/omega/wgdisk/taymur/sgy'

    if os.path.exists(patchName):
        simvols = set(['0','1','2','3','4','5','6','7','8','9'])
        for fname in sorted(os.listdir(patchName)):
            fcur = '{}/{}'.format(patchName, fname)
            fcurRoot, fcurExt = os.path.splitext(fcur)
            if not fcurRoot.endswith('_mod') and fcurExt == '.txt':
                print(fcur)
                baseName = os.path.basename(fcur)
                line = baseName[0:baseName.find('_Vel_')]
                f = open(fcur, 'r')
                fnew = open('{}_mod{}'.format(fcurRoot, fcurExt), 'w')
                fnew.write('{:<12} {:>12} {:>12} {:>12} {:>12} {:>12}\n'.format('Line', 'CMP', 'X', 'Y', 'TIME', 'VEL'))
                base = xcord = ycord = ''
                for s in f:
                    ls = s.split()
                    if len(ls) > 0:
                        if ls[0] != 'TIME' and ls[0][0] != '-':
                            if ls[0][0] in simvols:
                                fnew.write('{:<12} {:>12} {:>12} {:>12} {:>12} {:>12}\n'.format(line, base, xcord, ycord, ls[0], ls[1]))
                            else:
                                if ls[0][0] == 'C':
                                    base = ls[1]
                                elif ls[0][0] == 'Y':
                                    ycord = ls[1]
                                if len(ls) > 2:
                                    xcord = ls[3]
                fnew.close
                f.close


if __name__ == '__main__':
    main()
