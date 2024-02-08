#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

def main():
    dirName = r'/ud/zsolpatinskiy/surovyy2020/geometry_files/Grid'

    if dirName[-1] != '/':
        dirName += '/'
    if os.path.exists(dirName):
        files = os.listdir(dirName)
        gls = filter(lambda x: x.endswith('.gl'), files)
        fnew = open('{}GL_tbl.txt'.format(dirName), 'w')
        for gf in sorted(gls):
            print(gf)
            f = open(dirName + gf)
            tbl = []
            for s in f:
                ls = s.split()
                if ls != []:
                    if ls[0] == 'PRIM_ORDINAL':
                        tbl.append(float(ls[2]))
                    elif ls[0] == 'SECN_ORDINAL':
                        tbl.append(float(ls[2]))
                    elif ls[0] == 'PRIM_CELL_SIZE':
                        tbl.append(float(ls[2]))
                    elif ls[0] == 'SECN_CELL_SIZE':
                        tbl.append(float(ls[2]))
                    elif ls[0] == 'PRIM_ORDINAL_INC':
                        tbl.append(float(ls[2]))
                    elif ls[0] == 'SECN_ORDINAL_INC':
                        tbl.append(float(ls[2]))
                    elif ls[0] == "'MG1'":
                        tbl.append(float(ls[1]))
                        tbl.append(float(ls[2]))
                    elif ls[0] == "'MG2'":
                        tbl.append(float(ls[1]))
                        tbl.append(float(ls[2]))
                    elif ls[0] == "'MG3'":
                        tbl.append(float(ls[1]))
                        tbl.append(float(ls[2]))
                    elif ls[0] == "'MG4'":
                        tbl.append(float(ls[1]))
                        tbl.append(float(ls[2]))
            strW = ''
            for c in tbl[0:-1]:
                strW += str(c) + '\t'
            fnew.write('{}\t{}\n'.format(gf[0:-3], strW + str(tbl[-1])))
            f.close()

        fnew.close()
        print('Completed')
    else:
        print('Error')
        print('Каталог {} не найден'.format(dirName))


if __name__ == '__main__':
    main()
