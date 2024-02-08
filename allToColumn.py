#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from collections import defaultdict


file_name = r'c:\Data\ODData\hamakarskiy\Export\hor_pick.dat'
col = 0


def main():
    file_path = Path(file_name)
    if file_path.exists():
        data = defaultdict(list)
        with open(file_path, 'r') as f:
            for s in f:
                ls = s.split()
                if ls:
                    data[ls[col]].append(s)

        for line, line_data in data.items():
            with open(str(file_path.parent / f'{file_path.stem}_{line.replace('"', '')}{file_path.suffix}'), 'w') as f:
                for s in line_data:
                    f.write(s)


if __name__ == '__main__':
    main()
