#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path


def main():
    pattern_in = r'\\192.168.1.99\ud\ink23\hamakar\text_files\horizon\190614_hor*'
    min_station = '1'
    max_station = '99999'

    path_in = Path(Path(pattern_in).parent)
    pattern = Path(pattern_in).stem
    if path_in.exists():
        files = (path_in, ) if path_in.is_file() else sorted(list(file for file in path_in.glob(pattern) if not (file.stem.endswith('diff') or file.stem.endswith('dt'))))

        if files:
            diff_file_name = str(Path(path_in / f'{files[0].stem.split("_")[0]}_hor_diff.txt'))
            dt_file_name = str(Path(path_in / f'{files[0].stem.split("_")[0]}_hor_dt.txt'))
            with open(diff_file_name, 'w') as diff_f, open(dt_file_name, 'w') as dt_f:
                for i, file in enumerate(files):
                    with open(str(file), 'r') as in_f:
                        for j, s in enumerate(in_f):
                            line = s.split()
                            new_s = '\t'.join(line) + '\n'
                            if j == 0:
                                if i == 0:
                                    first_s = f'{min_station}\t{line[1]}\t{line[2]}\n'
                                    diff_f.write(first_s)
                                    dt_f.write(first_s)
                                dt_f.write(new_s)
                            diff_f.write(new_s)
                        dt_f.write(new_s)
                last_s = f'{max_station}\t{line[1]}\t{line[2]}\n'
                dt_f.write(last_s)
                diff_f.write(last_s)

        print('Completed!')


if __name__ == '__main__':
    main()
