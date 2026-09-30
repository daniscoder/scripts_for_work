#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re


def block_key(path):
    """Порядок по имени каталога с числами как числами: ..._block_2 раньше
    ..._block_10, а диск (fs0001, fs0008) в начале пути на порядок не влияет."""
    name = path.rstrip('/\\').replace('\\', '/').rsplit('/', 1)[-1]
    return [int(part) if part.isdigit() else part for part in re.split(r'(\d+)', name)]


if __name__ == '__main__':
    with open('paths.txt', 'r') as f:
        paths = [line.strip() for line in f if line.strip()]
    paths.sort(key=block_key)

    result = ' '.join(f'"{path}"' for path in paths)
    print(result)

    with open('paths_result.txt', 'w') as f:
        f.write(result)
