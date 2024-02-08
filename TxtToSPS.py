#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os


def main():
    patchName = r'u:\santalovskiy\santalovskiy\text_files\ARHIV\DOP'

    if os.path.exists(patchName):
        def txtToX(ls, fnew):
            fnew.write('X    {:>6}11{:<16}{:>8}1{:>4}{:>4}1{:<16}{:>8}{:>8}1\n'.format(ls[0], ls[1], ls[2], ls[3], ls[4], ls[5], ls[6], ls[7]))
        def txtToS(ls, fnew):
            fnew.write('S{:<16}{:>8}1                    {:>9}{:>10}{:>6}         \n'.format(ls[0], ls[1], ls[2], ls[3], ls[4]))
            # fnew.write('S{:<16}{:>8}1      {:>4}    {:>2}    {:>9}{:>10}{:>6}         \n'.format(ls[0], ls[1], ls[2], ls[3],ls[4], ls[5], ls[6]))
        def txtToR(ls, fnew):
            fnew.write('R{:<16}{:>8}1                    {:>9}{:>10}{:>6}         \n'.format(ls[0], ls[1], ls[2], ls[3], ls[4]))
        for fname in sorted(os.listdir(patchName)):
            fcur = '{}/{}'.format(patchName, fname)
            fcurRoot, fcurExt = os.path.splitext(fcur)
            if fcurExt == '.txt':
                txtToSPS = None
                xsr = fcurRoot[-1].lower()
                match xsr:
                    case 'x':
                        txtToSPS = txtToX
                    case 's':
                        txtToSPS = txtToS
                    case 'r':
                        txtToSPS = txtToR
                if txtToSPS != None:
                    fnewName = '{}.sps'.format(fcurRoot)
                    print(fcur, ' -> ', fnewName)
                    with open(fcur, 'r') as f, open(fnewName, 'w') as fnew:
                        for s in f:
                            ls = s.split()
                            if len(ls) > 0:
                                txtToSPS(ls, fnew)


if __name__ == '__main__':
    main()