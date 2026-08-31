#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Из файла LMO (f1) на каждый ПВ строим слоистую модель ВЧР, координаты X/Y
тянем из SPS (f2). За один прогон пишем оба файла — <f1>_offset.txt (границы
слоёв в удалениях, для расчёта статики по первым вступлениям) и
<f1>_speed.txt (скорости слоёв).

f1 — блок строк на каждый ПВ, номер ПВ только в первой строке блока:
    <ПВ> <мин.удаление> <макс.удаление> <интерсепт, мс> <скорость, м/с>
Строки блока — куски ОДНОГО непрерывного годографа первых вступлений: время
конца куска совпадает с временем начала следующего. Прямая волна в данных не
выделена, первый кусок — тоже преломлённая.

Модель: годограф приближается ломаной из четырёх прямых со свободными узлами,
скорость каждой прямой зажата в диапазон своего слоя (layers). Узлы ломаной и
есть границы слоёв в удалениях — то, ради чего всё и считается. Слой берётся в
модель, только если его диапазон скоростей пересекается с наблюдённым: на
коротком блоке слоёв выйдет меньше четырёх, лишние прямые не выдумываем.

Скорости МНК может упереть в край диапазона — значит данные хотят быстрее или
медленнее, чем задано в layers. Такие ПВ считаются, но их число печатается:
если их много, диапазон надо расширить, иначе границы слоёв смещены.

f2 — SPS с фиксированными позициями (нумерация с 1, границы включительно):
    2-17  линия ПВ, 18-25 точка ПВ (склеиваем без пробелов -> номер ПВ),
    47-55 X, 56-65 Y

Формат выхода — блок на слой, номер слоя только в первой строке блока:
    _offset:  <слой> <X> <Y> <мин.удаление> <макс.удаление>   со слоя 2
    _speed:   <слой> <X> <Y> <скорость>                       со слоя 1
Удаления округляются ВНИЗ с шагом round_step, скорости пишутся как есть.
"""

import math
from pathlib import Path

f1_path = r"d:\Processing\2026_Юкола-нефть\stat\refractionLayers\LMO_tabmashinskiy_2025.txt"
f2_path = r"d:\Processing\2026_Юкола-нефть\Тамбашинский\mesa\sps\tambashinskiy_2025.sps"
out_dir = r""           # пусто — класть рядом с f1

pv_col = 0              # колонка номера ПВ в f1
x1_col, x2_col = 1, 2   # мин./макс. удаление куска годографа
t0_col, v_col = 3, 4    # интерсепт (мс) и скорость (м/с) куска

round_step = 10         # шаг округления удалений (вниз)
max_offset = 3000.0     # дальнее удаление съёмки: в f1 последний кусок обычно
                        # тянется до 1.0E7, до бесконечности модель не считаем

# Слои модели: номер и диапазон скорости, м/с. Диапазоны не пересекаются и идут
# по возрастанию — на этом держится и подбор, и отбор слоёв под данные. Границы
# 3 и 4 слоя широкие: там скорость известна приблизительно (~3600 и ~4600), а
# упор в край диапазона тянет за собой и границу слоя в удалениях.
layers = (
    (1, 400.0, 1000.0),
    (2, 1400.0, 2200.0),
    (3, 3000.0, 4200.0),
    (4, 4400.0, 5600.0),
)

min_layer_width = 5.0   # слой уже этого по удалениям — повод для предупреждения
bad_rms = 10.0          # невязка модели с годографом выше — тоже

sps_line_pos = (2, 17)  # позиции линии ПВ в SPS (с 1, включительно)
sps_point_pos = (18, 25)
sps_x_pos = (47, 55)
sps_y_pos = (56, 65)


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
    """[(номер ПВ, [(x1, x2, t0, V), ...])] — блок кусков годографа на ПВ."""
    result = []
    seen = set()
    need_cols = max(x1_col, x2_col, t0_col, v_col)
    cur = None
    with open(path, 'r') as f:
        for num, s in enumerate(f, 1):
            ls = s.rstrip('\n').rstrip('\r').split('\t')
            if len(ls) <= need_cols:
                continue
            pv = norm_num(ls[pv_col])
            if pv:                          # первая строка блока
                if pv in seen:
                    print(f'f1, строка {num}: ПВ {pv} уже был — блок пропущен')
                    cur = None
                    continue
                seen.add(pv)
                cur = []
                result.append((pv, cur))
            if cur is None:                 # хвост от пропущенного блока
                continue
            try:
                piece = (float(ls[x1_col]), float(ls[x2_col]),
                         float(ls[t0_col]), float(ls[v_col]))
            except ValueError:
                print(f'f1, строка {num}: не число в нужной колонке — пропуск')
                continue
            if piece[1] <= piece[0] or piece[3] <= 0:
                print(f'f1, строка {num}: удаления или скорость не годятся — пропуск')
                continue
            cur.append(piece)
    return [(pv, sorted(pieces)) for pv, pieces in result if pieces]


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


def curve_lines(pieces: list) -> list:
    """Годограф как список прямых (x_кон, a, b): t = a + b*x, b = 1000/V."""
    return [(x2, t0, 1000.0 / v) for x1, x2, t0, v in pieces]


def pick(lines: list, x: float) -> tuple:
    """Прямая, накрывающая x (по правой границе); за концом — последняя."""
    for ln in lines:
        if x <= ln[0]:
            return ln
    return lines[-1]


def node_x(p: list, n: int, x_beg: float, x_end: float) -> list:
    """Удаления узлов ломаной: начало, границы слоёв, конец."""
    return [x_beg] + list(p[n + 1:]) + [x_end]


def model_lines(p: list, n: int, x_beg: float, x_end: float) -> list:
    """Ломаная модели по параметрам p = [времена узлов..., границы слоёв...].

    Параметры — времена в узлах, а не интерсепт со скоростями: время узла
    трогает только две соседние прямые, и покоординатный спуск по ним сходится,
    тогда как по связке (интерсепт, скорости) он застревал в овраге."""
    xs = node_x(p, n, x_beg, x_end)
    lines = []
    for i in range(n):
        b = (p[i + 1] - p[i]) / (xs[i + 1] - xs[i])
        lines.append((xs[i + 1], p[i] - b * xs[i], b))
    return lines


def sq_int(a: float, b: float, u: float, v: float) -> float:
    """Интеграл (a + b*x)^2 / x dx от u до v.

    Вес 1/x, а не равный по x: ближние слои занимают десятки метров из тысяч, с
    равным весом их вклад в невязку теряется и МНК жертвует ими ради дальних —
    первый слой уезжал на 700 м/с при наблюдённых 600, а его граница на 30 м
    при истинных 45. С весом 1/x каждая октава удалений весит одинаково."""
    return a * a * math.log(v / u) + 2.0 * a * b * (v - u) + b * b * (v * v - u * u) / 2.0


def misfit(curve: list, model: list, x_beg: float, x_end: float) -> float:
    """СКО модели от годографа, мс. Обе кривые кусочно-линейны, поэтому берём
    точный интеграл по объединению их изломов, без дискретизации."""
    edges = {x_beg, x_end}
    for ln in curve + model:
        if x_beg < ln[0] < x_end:
            edges.add(ln[0])
    edges = sorted(edges)
    total = 0.0
    for u, v in zip(edges, edges[1:]):
        mid = (u + v) / 2.0
        c = pick(curve, mid)
        m = pick(model, mid)
        total += sq_int(m[1] - c[1], m[2] - c[2], u, v)
    return math.sqrt(max(total, 0.0) / math.log(x_end / x_beg))


def used_layers(pieces: list) -> list:
    """Слои, к диапазону которых ближе всего хоть один кусок годографа.

    Слой, за который в данных не отвечает ни один кусок, в модель не берём: без
    этого на ПВ со скоростями 700-1800-4500 МНК втискивал третью прямую в зазор
    между 1800 и 4500 и выдавал границу слоя, которой в данных нет."""
    def dist(lay, v):
        return max(lay[1] - v, 0.0, v - lay[2])

    used = {min(layers, key=lambda lay: dist(lay, pc[3]))[0] for pc in pieces}
    return [lay for lay in layers if lay[0] in used]


def init_knots(pieces: list, lays: list, x_beg: float, x_end: float) -> list:
    """Стартовые узлы: там, где кажущаяся скорость впервые дотягивает до порога
    между диапазонами соседних слоёв."""
    knots = []
    for i in range(len(lays) - 1):
        thr = (lays[i][2] + lays[i + 1][1]) / 2.0
        x = x_end
        for x1, x2, t0, v in pieces:
            if v >= thr:
                x = min(max(x1, x_beg), x_end)
                break
        knots.append(x)
    # зазор нужен только чтобы узлы не слиплись: разносить их равномерно по
    # всему диапазону нельзя — спуск потом не вытащит первый узел с сотен метров
    n = len(knots)
    gap = min(min_layer_width, (x_end - x_beg) / (2.0 * (n + 1)))
    for i in range(n):                      # строго по возрастанию, с зазором
        lo = x_beg + gap * (i + 1)
        if i:
            lo = max(lo, knots[i - 1] + gap)
        knots[i] = min(max(knots[i], lo), x_end - gap * (n - i))
    return knots


def moves(p: list, k: int, s: float, n: int, lines: list) -> list:
    """Пробные шаги по параметру k: вперёд, назад и — для границы слоя — сдвиг
    вдоль соседней прямой.

    Без сдвига вдоль прямой граница стоит намертво: сдвинуть её при неподвижном
    времени в узле значит сразу сломать обе соседние скорости, и спуск застревал
    в стартовой точке."""
    out = []
    for d in (s, -s):
        q = list(p)
        q[k] += d
        out.append(q)
        if k > n:                           # k — граница слоя, узел k-n
            j = k - n - 1
            for b in (lines[j][2], lines[j + 1][2]):
                q2 = list(p)
                q2[k] += d
                q2[j + 1] += b * d
                out.append(q2)
    return out


def fit(pieces: list, lays: list, x_beg: float, x_end: float) -> tuple:
    """Подбор ломаной покоординатным спуском. Возвращает (границы, скорости, СКО).

    Параметры МНК: времена в узлах и удаления границ слоёв. Скорость каждой
    прямой зажата в диапазон своего слоя, границы — в [x_beg, x_end] и строго по
    возрастанию."""
    n = len(lays)
    curve = curve_lines(pieces)
    knots = init_knots(pieces, lays, x_beg, x_end)
    xs = [x_beg] + knots + [x_end]

    # старт: ведём время по годографу, но шаг между узлами зажимаем в диапазон
    # скорости слоя — иначе стартовая точка может оказаться недопустимой
    times = [pick(curve, x_beg)[1] + pick(curve, x_beg)[2] * x_beg]
    for i in range(n):
        want = pick(curve, xs[i + 1])[1] + pick(curve, xs[i + 1])[2] * xs[i + 1]
        dx = xs[i + 1] - xs[i]
        b = min(max((want - times[i]) / dx, 1000.0 / lays[i][2]), 1000.0 / lays[i][1])
        times.append(times[i] + b * dx)
    p = times + knots
    step = [5.0] * (n + 1) + [(x_end - x_beg) / 20.0] * (n - 1)

    def cost(q):
        return misfit(curve, model_lines(q, n, x_beg, x_end), x_beg, x_end)

    def feasible(q):
        xq = node_x(q, n, x_beg, x_end)
        for i in range(n):
            if xq[i + 1] - xq[i] <= 0.0 or q[i + 1] - q[i] <= 0.0:
                return False
            v = 1000.0 * (xq[i + 1] - xq[i]) / (q[i + 1] - q[i])
            if not lays[i][1] <= v <= lays[i][2]:
                return False
        return True

    best = cost(p)
    for _ in range(300):
        moved = False
        lines = model_lines(p, n, x_beg, x_end)
        for k in range(len(p)):
            for q in moves(p, k, step[k], n, lines):
                if not feasible(q):
                    continue
                c = cost(q)
                if c < best - 1e-9:
                    best, p, moved = c, q, True
                    break
        if not moved:
            step = [s / 2.0 for s in step]
            if max(step) < 1e-4:
                break
    xs = node_x(p, n, x_beg, x_end)
    vels = [1000.0 * (xs[i + 1] - xs[i]) / (p[i + 1] - p[i]) for i in range(n)]
    return list(p[n + 1:]), vels, best


def build(pieces: list) -> tuple:
    """(слои, СКО) для одного ПВ. Слой — (номер, V, удаление от, удаление до)."""
    lays = used_layers(pieces)
    x_beg = max(pieces[0][0], 0.1)      # вес 1/x в невязке нуля не терпит
    x_end = min(max(pc[1] for pc in pieces), max_offset)
    if not lays or x_end - x_beg < min_layer_width:
        return [], None
    if len(lays) == 1:
        return [(lays[0][0], pieces[0][3], x_beg, x_end)], 0.0
    knots, vels, rms = fit(pieces, lays, x_beg, x_end)
    bounds = [x_beg] + list(knots) + [x_end]
    return [(lays[i][0], vels[i], bounds[i], bounds[i + 1])
            for i in range(len(lays))], rms


def floor_step(v: float) -> int:
    return int(math.floor(v / round_step)) * round_step


def write_blocks(path: Path, rows: list, first_layer: int, fmt) -> int:
    """Блок на слой, номер слоя только в первой строке своего блока."""
    written = 0
    with open(path, 'w') as f:
        for lay_def in layers:
            num = lay_def[0]
            if num < first_layer:
                continue
            head = True
            for pv, x, y, lay in rows:
                if lay[0] != num:
                    continue
                f.write('{}\t{}\n'.format(num if head else '', fmt(x, y, lay)))
                head = False
                written += 1
    return written


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

    rows = []           # (ПВ, X, Y, (слой, V, от, до)) — по строке на слой
    missed, empty, pinned, thin, rough = [], [], [], [], []
    for pv, pieces in data:
        xy = coords.get(pv)
        if xy is None:
            missed.append(pv)
            continue
        model, rms = build(pieces)
        if not model:
            empty.append(pv)
            continue
        if rms is not None and rms > bad_rms:
            rough.append((rms, pv))
        for lay in model:
            num, v, x_from, x_to = lay
            band = layers[num - 1]
            if min(abs(v - band[1]), abs(v - band[2])) < 1.0:
                pinned.append(pv)
            if x_to - x_from < min_layer_width:
                thin.append(pv)
            rows.append((pv, xy[0], xy[1], lay))

    parent = Path(out_dir).absolute() if out_dir else path_1.parent

    path_off = parent / f'{path_1.stem}_offset.txt'
    n_off = write_blocks(
        path_off, rows, 2,
        lambda x, y, lay: '{:.1f}\t{:.1f}\t{}\t{}'.format(
            x, y, floor_step(lay[2]), floor_step(lay[3])))
    print(f'удаления: записано {n_off} строк -> {path_off}')

    path_spd = parent / f'{path_1.stem}_speed.txt'
    n_spd = write_blocks(
        path_spd, rows, 1,
        lambda x, y, lay: '{:.1f}\t{:.1f}\t{:.1f}'.format(x, y, lay[1]))
    print(f'скорости: записано {n_spd} строк -> {path_spd}')

    if missed:
        print(f'Нет координат для {len(missed)} ПВ: {", ".join(missed[:20])}'
              f'{" ..." if len(missed) > 20 else ""}')
    if empty:
        print(f'Не из чего строить модель, {len(empty)} ПВ: {", ".join(empty[:20])}')
    if pinned:
        uniq = sorted(set(pinned))
        print(f'Скорость упёрлась в край диапазона на {len(uniq)} ПВ — '
              f'диапазоны в layers стоит расширить: {", ".join(uniq[:20])}')
    if thin:
        uniq = sorted(set(thin))
        print(f'Слой уже {min_layer_width:.0f} м на {len(uniq)} ПВ: '
              f'{", ".join(uniq[:20])}')
    if rough:
        rough.sort(reverse=True)
        print(f'Невязка модели больше {bad_rms:.0f} мс на {len(rough)} ПВ, худшие: '
              + ', '.join(f'{pv} ({r:.1f} мс)' for r, pv in rough[:10]))


if __name__ == '__main__':
    main()
