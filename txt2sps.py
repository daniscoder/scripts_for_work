#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from collections import defaultdict

path_or_file = r"c:\Processing\Tallinskiy\sps\geom_target.txt"

ffid_name = 'IDENT_NUM'
s_line_name = 'SOURCE_LINE_ID'
s_point_name = 'SOURCE_POINT_ID'
r_line_name = 'DETECT_LINE_ID'
r_point_name = 'DETECT_POINT_ID'
s_x_name = 'XCORD_SOURCE'
s_y_name = 'YCORD_SOURCE'
r_x_name = 'XCORD_DETECT'
r_y_name = 'YCORD_DETECT'

def check_string_number(s):
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s


def txt_to_data(path: str) -> list:
    result = []
    with open(path, 'r') as f:
        for s in f:
            ls = s.split()
            if ls:
                result.append(tuple(check_string_number(elem) for elem in ls))
    return result


def main():
    path_in = Path(path_or_file).absolute()
    if path_in.exists():

        for file_path in (path_in, ) if path_in.is_file() else sorted(list(file for file in path_in.glob('*' if path_in.is_dir() else path_in.stem))):
            data = txt_to_data(str(file_path))

            headers = {elem: i for i, elem in enumerate(data[0])}
            ffid_col = headers.get(ffid_name)
            s_line_col = headers.get(s_line_name)
            s_point_col = headers.get(s_point_name)
            r_line_col = headers.get(r_line_name)
            r_point_col = headers.get(r_point_name)
            s_x_col = headers.get(s_x_name)
            s_y_col = headers.get(s_y_name)
            r_x_col = headers.get(r_x_name)
            r_y_col = headers.get(r_y_name)

            s_data = {}
            r_data = {}
            ffid_data = {}
            pattern_data = defaultdict(lambda: defaultdict(list))

            if not ffid_col is None and not s_line_col is None and not s_point_col is None and not r_line_col is None and not r_point_col is None:
                for row_data in data[1:]:
                    s_num = f'{row_data[s_line_col]}{row_data[s_point_col]}'
                    r_num = f'{row_data[r_line_col]}{row_data[r_point_col]}'
                    ffid_domain = f'{row_data[ffid_col]}_{s_num}'

                    if s_num not in s_data:
                        s_data[s_num] = (row_data[s_line_col], row_data[s_point_col], row_data[s_x_col], row_data[s_y_col])

                    if r_num not in r_data:
                        r_data[r_num] = (row_data[r_line_col], row_data[r_point_col], row_data[r_x_col], row_data[r_y_col])

                    if ffid_domain not in ffid_data:
                        ffid_data[ffid_domain] = (row_data[ffid_col], s_num)

                    pattern_data[ffid_domain][row_data[r_line_col]].append(row_data[r_point_col])

            out_path = str(Path(file_path.parent) / f'{file_path.stem}')

            if s_data:
                with open(f'{out_path}_s.sps', 'w') as f:
                    for row in s_data.values():
                        f.write('S{:<16}{:>8}1                    {:>9}{:>10}{:>6}         \n'.format(row[0], row[1], row[2], row[3], 0))

            if r_data:
                with open(f'{out_path}_r.sps', 'w') as f:
                    for row in r_data.values():
                        f.write('S{:<16}{:>8}1                    {:>9}{:>10}{:>6}         \n'.format(row[0], row[1], row[2], row[3], 0))

            if pattern_data:
                with open(f'{out_path}_x.sps', 'w') as f:
                    for ffid_domain, patterns in pattern_data.items():
                        r_lines = sorted(patterns.keys())
                        trc = 1
                        for r_line in r_lines:
                            r_points = sorted(patterns[r_line])
                            r_point_start = None
                            r_point_prep = r_points[0]
                            r_point_count = len(r_points)
                            for i, r_point in enumerate(r_points):
                                if r_point_start is None:
                                    r_point_start = r_point
                                if r_point > r_point_prep + 1 or i + 1 == r_point_count:
                                    point_change = r_point - r_point_start
                                    f.write('X    {:>6}11{:<16}{:>8}1{:>4}{:>4}1{:<16}{:>8}{:>8}1\n'.format(
                                        ffid_data[ffid_domain][0], s_data[ffid_data[ffid_domain][1]][0], s_data[ffid_data[ffid_domain][1]][1],
                                        trc, trc + point_change, r_line, r_point_start, r_point))
                                    trc = trc + point_change + 1
                                r_point_prep = r_point

        print('Completed!')


if __name__ == '__main__':
    main()