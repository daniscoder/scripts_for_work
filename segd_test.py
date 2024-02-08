#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

def main():
    pathIn = r'\\dl5\gpfs\2D\OPR2019\SS\InData\20220311'
    header_len = 4640

    if os.path.exists(pathIn):
        if os.path.isfile(pathIn):
            listfile = [os.path.split(pathIn)[1]]
            path = os.path.dirname(pathIn)
        else:
            listfile = sorted([elem for elem in os.listdir(pathIn) if elem.endswith('.segd')])
            path = pathIn

        for filename in listfile:
            curname = os.path.join(path, filename)
            fname, fext = os.path.splitext(curname)

            outname = f'{fname}_mod{fext}'
            with open(curname, 'rb') as f, open(outname, 'wb') as fnew:
                f.read(header_len)
                fnew.write(f.read())


if __name__ == '__main__':
    main()