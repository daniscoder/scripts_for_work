#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

def main():
    pathIn = r'C:\Users\danis\PycharmProjects\test'

    if os.path.exists(pathIn):
        isfile = os.path.isfile(pathIn)
        if isfile:
            listfile = (os.path.split(pathIn)[1], )
            path = os.path.dirname(pathIn)
        else:
            listfile = sorted(os.listdir(pathIn))
            path = pathIn
        for filename in listfile:
            curname = os.path.join(path, filename)
            fname, fext = os.path.splitext(curname)
            if isfile or (not fname.endswith('_gen') and fext == '.txt'):
                outname = f'{fname}_gen{fext}'
                with open(curname, 'r') as f, open(outname, 'w') as fnew:
                    cmp = None
                    for s in f:
                        ls = s.split()
                        if ls[2] != cmp:
                            cmp = ls[2]
                            fnew.write('{}\tNOT_USED\t{}\t{}\n'.format(cmp, ls[3], ls[4]))
                        else:
                            fnew.write('\t\t{}\t{}\n'.format(ls[3], ls[4]))
                print(curname, '->', outname)
        print('Completed!')

if __name__ == '__main__':
    main()