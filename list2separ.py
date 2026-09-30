#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
from pathlib import Path

# Вход и результат - в песочнице рядом со скриптом, откуда бы его ни запустили
SANDBOX = Path(__file__).resolve().parent / 'sandbox'


def block_key(path):
    """Порядок по имени каталога с числами как числами: ..._block_2 раньше
    ..._block_10, а диск (fs0001, fs0008) в начале пути на порядок не влияет."""
    name = path.rstrip('/\\').replace('\\', '/').rsplit('/', 1)[-1]
    return [int(part) if part.isdigit() else part for part in re.split(r'(\d+)', name)]


if __name__ == '__main__':
    src = SANDBOX / 'paths.txt'
    if not src.exists():
        SANDBOX.mkdir(exist_ok=True)
        src.touch()
        print(f'Вставьте пути по одному в строке в {src} и запустите еще раз')
        raise SystemExit(1)
    with open(src, 'r') as f:
        paths = [line.strip() for line in f if line.strip()]
    paths.sort(key=block_key)

    result = ' '.join(f'"{path}"' for path in paths)
    print(result)

    with open(SANDBOX / 'paths_result.txt', 'w') as f:
        f.write(result)
