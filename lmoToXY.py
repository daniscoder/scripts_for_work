#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Из файла LMO (f1) берём номер ПВ, максимальное удаление и скорость первой
строки пары, координаты X/Y тянем из SPS (f2). За один прогон пишем оба
файла — <f1>_offset.txt и <f1>_speed.txt.

f1 — на каждый ПВ по две строки, нужна только первая:
    <ПВ> <мин.удаление> <макс.удаление> <время> <скорость>
    (у второй строки колонка ПВ пустая — по этому её и отличаем)

f2 — SPS с фиксированными позициями (нумерация с 1, границы включительно):
    2-17  линия ПВ, 18-25 точка ПВ (склеиваем без пробелов -> номер ПВ),
    47-55 X, 56-65 Y

Удаление округляется ВНИЗ с шагом 10, скорость — обычным округлением
до ближайшего, шаг тот же.
"""

import math
from pathlib import Path

f1_path = r"d:\Processing\2026_Юкола-нефть\stat\refractionLayers\LMO_tabmashinskiy_2025.txt"
f2_path = r"d:\Processing\2026_Юкола-нефть\Тамбашинский\mesa\sps\tambashinskiy_2025.sps"
out_dir = r""           # пусто — класть рядом с f1

pv_col = 0              # колонка номера ПВ в f1
round_step = 10         # шаг округления величины

sps_line_pos = (2, 17)  # позиции линии ПВ в SPS (с 1, включительно)
sps_point_pos = (18, 25)
sps_x_pos = (47, 55)
sps_y_pos = (56, 65)

# суффикс файла: (что пишем, колонка в f1, как округляем)
kinds = (
    ('offset', 'удаление', 2, lambda v: math.floor(v / round_step)),
    ('speed', 'скорость', 4, lambda v: math.floor(v / round_step + 0.5)),
)


def field(s: str, pos: tuple) -> str:
    """Кусок строки по позициям SPS (нумерация с 1, обе границы включительно)."""
    return s[pos[0] - 1:pos[1]].strip()


def norm_num(s: str) -> str:
    """Номер линии/точки без пробелов и без хвостового .0 — иначе 1149.0 не
    склеится с 1149 из f1 и ПВ молча потеряется."""
    s = s.replace(' ', '')
    if '.' in s:
        s = s.rstrip('0').rstrip('.')
    return s


def read_f1(path: Path) -> list:
    """[(номер ПВ, [величина по каждому виду])] — только первые строки пар."""
    result = []
    seen = set()
    need_cols = max(kind[2] for kind in kinds)
    with open(path, 'r') as f:
        for num, s in enumerate(f, 1):
            ls = s.rstrip('\n').rstrip('\r').split('\t')
            if len(ls) <= need_cols:
                continue
            pv = norm_num(ls[pv_col])
            if not pv:                      # вторая строка пары
                continue
            if pv in seen:
                continue
            try:
                values = [float(ls[kind[2]]) for kind in kinds]
            except ValueError:
                print(f'f1, строка {num}: не число в нужной колонке — пропуск')
                continue
            seen.add(pv)
            result.append((pv, values))
    return result


def read_f2(path: Path) -> dict:
    """{номер ПВ: (X, Y)}"""
    result = {}
    with open(path, 'r') as f:
        for num, s in enumerate(f, 1):
            s = s.rstrip('\n').rstrip('\r')
            if not s.strip() or s[0] in ('H', 'h'):
                continue
            if len(s) < sps_y_pos[1]:
                print(f'f2, строка {num}: короче {sps_y_pos[1]} символов — пропуск')
                continue
            pv = norm_num(field(s, sps_line_pos)) + norm_num(field(s, sps_point_pos))
            try:
                x = float(field(s, sps_x_pos))
                y = float(field(s, sps_y_pos))
            except ValueError:
                print(f'f2, строка {num}: не читаются координаты — пропуск')
                continue
            if pv not in result:
                result[pv] = (x, y)
    return result


def main():
    path_1 = Path(f1_path).absolute()
    path_2 = Path(f2_path).absolute()

    for p in (path_1, path_2):
        if not p.exists():
            print(f'Нет файла: {p}')
            return

    data = read_f1(path_1)
    coords = read_f2(path_2)
    print(f'f1: ПВ {len(data)}, f2: точек {len(coords)}')

    parent = Path(out_dir).absolute() if out_dir else path_1.parent

    missed = []
    for i, (suffix, title, _, round_fn) in enumerate(kinds):
        path_out = parent / f'{path_1.stem}_{suffix}.txt'
        written = 0
        missed = []
        with open(path_out, 'w') as f:
            for pv, values in data:
                xy = coords.get(pv)
                if xy is None:
                    missed.append(pv)
                    continue
                f.write('{:.1f}\t{:.1f}\t{}\n'.format(
                    xy[0], xy[1], int(round_fn(values[i])) * round_step))
                written += 1
        print(f'{title}: записано {written} строк -> {path_out}')

    if missed:
        print(f'Нет координат для {len(missed)} ПВ: {", ".join(missed[:20])}'
              f'{" ..." if len(missed) > 20 else ""}')


if __name__ == '__main__':
    main()
