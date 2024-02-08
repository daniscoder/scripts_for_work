#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

def main():
    filename = r'/mp/home/danis/Downloads/raport.obs'

    if os.path.exists(filename):
        fname, fext = os.path.splitext(filename)
        fopen = open(filename, 'r')
        fnew = open('{}_{}{}'.format(fname, 'X', fext), 'w')
        simvols = set(['0','1','2','3','4','5','6','7','8','9'])
        for s in fopen:
            if s[0] in simvols:
                ls = s.split('\t')
                w1 = 'X0{:>9}11{:<16}{:>8}1'.format(ls[0], int(ls[4].replace('.0', '')), ls[5].replace('.0', ''))
                for sub in ls[28].split():
                    f = 0
                    d = True
                    toS = False
                    for i, c in enumerate(sub):
                        if c == ':':
                            line = sub[f:i]
                            detF_i = i + 1
                        elif c == '-':
                            if d:
                                detF = sub[detF_i: i]
                                detL_i = i + 1
                            else:
                                trsF = sub[trcF_i: i]
                                trcL_i = i + 1
                            toS = True
                        elif c == '(':
                            if toS:
                                detL = sub[detL_i: i]
                            else:
                                detF = detL = sub[detF_i: i]
                            trcF_i = i + 1
                            toS = False
                            d = False
                        elif c == ')':
                            if toS:
                                trcL = sub[trcL_i: i]
                            else:
                                trcF = trcL = sub[trcF_i: i]
                            detF_i = i + 1
                            f = i + 1
                            toS = False
                            d = True
                            fnew.write(w1 + '{:>4}{:>4}1{:<16}{:>8}{:>8}1\n'.format(trsF, trcL, line, detF, detL))

        fnew.close()
        fopen.close()


if __name__ == '__main__':
    main()
