#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

def main():
    fName = r'/ud/zsolpatinskiy/surovyy2020/sfm_tables/hor/hor_forVarWin'
    startWin = 100
    startVel = 2500
    endVel = 2500
    ower = 200
    minWinLength = 604

    dirName, fMask = os.path.split(fName)
    if os.path.exists(dirName):
        files = filter(lambda x: x.startswith(fMask), os.listdir(dirName))
        for f in sorted(files):
            fcur = '{}/{}'.format(dirName, f)
            fcurRoot, fcurExt = os.path.splitext(fcur)
            if not fcurRoot.endswith('_Res'):
                print(f)
                ff = open(fcur)
                fnew = open('{}_Res{}'.format(fcurRoot, fcurExt), 'w')
                fLine = "Window{}\t'ZERO'\t'YES'\t'ABS'\t{}\t'HYPERBOLIC'\t{}\t{}\t0.0\t'HYPERBOLIC'\t{}\t{}\t0.0\n"
                lLine = "\t\t\t\t{}\t'HYPERBOLIC'\t{}\t{}\t0.0\t'HYPERBOLIC'\t{}\t{}\t0.0\n"
                def get_end_win(sWin, eWin):
                    return max(eWin, sWin + minWinLength)
                for i, s in enumerate(ff):
                    ls = s.split()
                    if i == 0:
                        win1 = fLine.format(1, ls[0], startWin, startVel, get_end_win(startWin, int(ls[1])), endVel)
                        win2 = fLine.format(2, ls[0], int(ls[1]) - ower, startVel, get_end_win(int(ls[1]), int(ls[2])), endVel)
                    else:
                        win1 += lLine.format(ls[0], startWin, startVel, get_end_win(startWin, int(ls[1])), endVel)
                        win2 += lLine.format(ls[0], int(ls[1]) - ower, startVel, get_end_win(int(ls[1]), int(ls[2])), endVel)
                fnew.write(win1 + win2)
                ff.close()
                fnew.close()
        print('Completed')
    else:
        print('Error')
        print('Каталог {} не найден'.format(dirName))


if __name__ == '__main__':
    main()
