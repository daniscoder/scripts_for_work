#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Из файла LMO (f1) на каждый ПВ строим слоистую модель ВЧР, координаты X/Y
тянем из SPS (f2). За один прогон пишем оба файла — <f1>_offset.txt (границы
слоёв в удалениях, для расчёта статики по первым вступлениям) и
<f1>_speed.txt (скорости слоёв).

Настройки задаются в окне (PySide6), значения по умолчанию — в Config. Счёт от
интерфейса отделён: run(cfg, log) работает и без Qt, если импортировать модуль.

f1 — блок строк на каждый ПВ, номер ПВ только в первой строке блока:
    <ПВ> <мин.удаление> <макс.удаление> <интерсепт, мс> <скорость, м/с>
Строки блока — куски ОДНОГО непрерывного годографа первых вступлений: время
конца куска совпадает с временем начала следующего. Прямая волна в данных не
выделена, первый кусок — тоже преломлённая.

Границы слоёв в удалениях — то, ради чего всё и считается, — берутся одним из
двух способов (настройка method):
    'lsq'       годограф приближается ломаной, по прямой на слой, со свободными
                узлами, скорость каждой прямой зажата в диапазон своего слоя.
                Узлы ломаной и есть границы; учитываются и времена, и скорости;
    'threshold' граница там, где кажущаяся скорость пересекает порог между
                диапазонами соседних слоёв, с интерполяцией внутри перехода.
                Времена не участвуют вовсе.
Скорость слоя в обоих способах считается МНК по его собственному окну и в
диапазон не зажимается: окно уже определено, и подгонять под него ещё и скорость
значило бы врать в отчёте. Выход скорости за диапазон пишется в отчёт — это
признак, что граница проведена не там.

Оба способа обязаны отдать кусок годографа тому слою, в чей диапазон попадает
его скорость: в окно второго слоя не должны попадать удаления, где в первых
вступлениях ещё первый слой. Свобода у границы остаётся только внутри кусков,
скорость которых лежит в зазоре между диапазонами и не принадлежит никому.

Слой берётся в модель, только если к его диапазону ближе хоть один кусок
годографа. Счёт статики требует одинакового числа слоёв на всех ПВ, поэтому
слой, которого в данных нет, по умолчанию пишется вырожденным окном нулевой
ширины (настройка missing: 'degenerate' | 'all' | 'skip').

Скорость может упереться в край диапазона — значит данные хотят быстрее или
медленнее, чем задано. Такие ПВ считаются, но их число печатается: если их
много, диапазон надо расширить, иначе границы слоёв смещены.

f2 — SPS с фиксированными позициями (нумерация с 1, границы включительно):
    2-17  линия ПВ, 18-25 точка ПВ (склеиваем без пробелов -> номер ПВ),
    47-55 X, 56-65 Y

Формат выхода — блок на слой, номер слоя только в первой строке блока:
    _offset:  <слой> <X> <Y> <мин.удаление> <макс.удаление>   со слоя 2
    _speed:   <слой> <X> <Y> <скорость>                       со слоя 1
Удаления округляются с шагом round_step: обычным округлением или сжатием окна
внутрь (round_mode), скорости пишутся как есть.
"""

import math
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QSettings, QThread, Qt, Signal, Slot
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox,
                               QDoubleSpinBox,
                               QFileDialog, QFormLayout, QGridLayout,
                               QGroupBox, QHBoxLayout, QHeaderView, QLabel,
                               QLineEdit, QMessageBox, QPlainTextEdit,
                               QPushButton, QSpinBox, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)


class Config:
    """Все настройки счёта в одном месте: то же самое правится в окне."""

    def __init__(self):
        self.f1_path = r"d:\Processing\2026_Юкола-нефть\stat\refractionLayers\LMO_tabmashinskiy_2025.txt"
        self.f2_path = r"d:\Processing\2026_Юкола-нефть\Тамбашинский\mesa\sps\tambashinskiy_2025.sps"
        self.out_dir = r""          # пусто — класть рядом с f1

        self.pv_col = 0             # колонка номера ПВ в f1
        self.x1_col = 1             # мин. удаление куска годографа
        self.x2_col = 2             # макс. удаление
        self.t0_col = 3             # интерсепт, мс
        self.v_col = 4              # скорость, м/с

        self.round_step = 10        # шаг округления удалений
        self.round_mode = 'near'    # 'near' — обе границы к ближайшему узлу
                                    # сетки, 'in' — окно внутрь: минимум вверх,
                                    # максимум вниз
        self.min_offset = 10        # ближнее удаление съёмки. В f1 первый кусок
                                    # начинается с 1 м, и если у ПВ нет первого
                                    # слоя, окно второго стартовало с этой
                                    # единицы и после округления вниз давало 0
        self.max_offset = 3000.0    # дальнее удаление съёмки: в f1 последний
                                    # кусок обычно тянется до 1.0E7, до
                                    # бесконечности модель не считаем

        # Слои модели: номер и диапазон скорости, м/с. Нумерация подряд с 1,
        # диапазоны не перекрываются и идут по возрастанию — на этом держится и
        # подбор, и отбор слоёв под данные. Второй и третий стыкуются вплотную
        # на 2200: всё быстрее уходит в третий слой, а упор скорости ровно в это
        # число значит лишь, что по данным граница между ними не определяется
        # однозначно, и расширять там нечего.
        self.layers = [
            (1, 400.0, 1200.0),
            (2, 1200.0, 2200.0),
            (3, 2200.0, 5600.0),
        ]

        # Чем считать границы слоёв:
        #   'lsq'       — годограф приближается ломаной, по прямой на слой, узлы
        #                 свободны, скорость каждой зажата в диапазон своего
        #                 слоя. Границы выходят из наилучшего приближения всего
        #                 годографа сразу, в счёт идут и времена, и скорости;
        #   'threshold' — граница там, где кажущаяся скорость пересекает порог
        #                 между диапазонами соседних слоёв, с интерполяцией
        #                 внутри перехода. Времена не участвуют вовсе.
        # Кусок годографа в любом случае достаётся слою, в чей диапазон попала
        # его скорость (knot_limits), поэтому при смежных диапазонах способы
        # дают одни и те же границы — разойтись им есть где только в зазорах
        # между диапазонами.
        self.method = 'lsq'

        # Что делать со слоем, которого в данных нет (ни один кусок годографа
        # не попадает к нему ближе, чем к соседям). Счёт статики требует
        # одинакового числа слоёв на всех ПВ, поэтому по умолчанию слой не
        # пропускается, а пишется вырожденным окном нулевой ширины:
        #   'degenerate' — окно схлопнуто в границу соседних слоёв, скорость
        #                  берётся серединой диапазона. Слоёв всегда поровну,
        #                  и видно, что вступлений у слоя нет;
        #   'all'        — подбор всегда ведётся всеми слоями. Окно выйдет
        #                  ненулевым, но его границы взяты не из данных;
        #   'skip'       — слой не пишется вовсе. Число слоёв по ПВ разное.
        self.missing = 'degenerate'

        self.min_layer_width = 5.0  # слой уже этого по удалениям — в отчёт
        self.bad_rms = 10.0         # невязка модели с годографом выше — тоже

        self.sps_line_pos = (2, 17)     # позиции линии ПВ в SPS (с 1, вкл.)
        self.sps_point_pos = (18, 25)
        self.sps_x_pos = (47, 55)
        self.sps_y_pos = (56, 65)


def check_layers(lays: list) -> str:
    """Текст ошибки или пустая строка. Диапазоны должны идти по возрастанию и не
    перекрываться: иначе кусок годографа достаётся сразу двум слоям и подбор
    теряет смысл."""
    if not lays:
        return 'Не задано ни одного слоя'
    for i, (num, lo, hi) in enumerate(lays, 1):
        if num != i:
            return (f'Слои нумеруются подряд с 1, а {i}-й по счёту назван {num}: '
                    'иначе в выход уходит слой с чужим номером')
        if lo >= hi:
            return f'Слой {num}: нижняя скорость не меньше верхней'
    for a, b in zip(lays, lays[1:]):
        if a[2] > b[1]:
            return f'Слои {a[0]} и {b[0]}: диапазоны скоростей перекрываются'
    return ''


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


def read_f1(path: Path, cfg: Config, log) -> list:
    """[(номер ПВ, [(x1, x2, t0, V), ...])] — блок кусков годографа на ПВ."""
    result = []
    seen = set()
    cols = (cfg.x1_col, cfg.x2_col, cfg.t0_col, cfg.v_col)
    need_cols = max(cols)
    cur = None
    with open(path, 'r') as f:
        for num, s in enumerate(f, 1):
            ls = s.rstrip('\n').rstrip('\r').split('\t')
            if len(ls) <= need_cols:
                continue
            pv = norm_num(ls[cfg.pv_col])
            if pv:                          # первая строка блока
                if pv in seen:
                    log(f'f1, строка {num}: ПВ {pv} уже был — блок пропущен')
                    cur = None
                    continue
                seen.add(pv)
                cur = []
                result.append((pv, cur))
            if cur is None:                 # хвост от пропущенного блока
                continue
            try:
                piece = tuple(float(ls[c]) for c in cols)
            except ValueError:
                log(f'f1, строка {num}: не число в нужной колонке — пропуск')
                continue
            if piece[1] <= piece[0] or piece[3] <= 0:
                log(f'f1, строка {num}: удаления или скорость не годятся — пропуск')
                continue
            cur.append(piece)
    return [(pv, sorted(pieces)) for pv, pieces in result if pieces]


def read_f2(path: Path, cfg: Config, log) -> dict:
    """{номер ПВ: (X, Y)}"""
    result = {}
    with open(path, 'r') as f:
        for num, s in enumerate(f, 1):
            s = s.rstrip('\n').rstrip('\r')
            if not s.strip() or s[0] in ('H', 'h'):
                continue
            if len(s) < cfg.sps_y_pos[1]:
                log(f'f2, строка {num}: короче {cfg.sps_y_pos[1]} символов — пропуск')
                continue
            pv = (norm_num(field(s, cfg.sps_line_pos))
                  + norm_num(field(s, cfg.sps_point_pos)))
            try:
                x = float(field(s, cfg.sps_x_pos))
                y = float(field(s, cfg.sps_y_pos))
            except ValueError:
                log(f'f2, строка {num}: не читаются координаты — пропуск')
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


def band_dist(lay: tuple, v: float) -> float:
    """Насколько скорость v не дотягивает до диапазона слоя (0 — внутри)."""
    return max(lay[1] - v, 0.0, v - lay[2])


def used_layers(pieces: list, lays: list, missing: str) -> list:
    """Слои, к диапазону которых ближе всего хоть один кусок годографа.

    Слой, за который в данных не отвечает ни один кусок, в подбор не берём: без
    этого на ПВ со скоростями 700-1800-4500 МНК втискивал третью прямую в зазор
    между 1800 и 4500 и выдавал границу слоя, которой в данных нет. В режиме
    'all' это как раз и нужно — слои подбираются все, лишь бы их число было
    одинаковым на всех ПВ."""
    if missing == 'all':
        return list(lays)
    used = {min(lays, key=lambda lay: band_dist(lay, pc[3]))[0] for pc in pieces}
    return [lay for lay in lays if lay[0] in used]


def pad_missing(model: list, lays: list, x_beg: float, x_end: float) -> list:
    """Дописать недостающие слои вырожденным окном нулевой ширины.

    Счёт статики требует одинакового числа слоёв на всех ПВ, а брать удаления
    отсутствующему слою неоткуда: схлопываем его окно в границу соседей, скорость
    берём серединой диапазона — по нулевой ширине сразу видно, что вступлений у
    слоя нет."""
    have = {lay[0]: lay for lay in model}
    out = []
    for num, lo, hi in lays:
        if num in have:
            out.append(have[num])
            continue
        after = [lay for lay in model if lay[0] > num]
        before = [lay for lay in model if lay[0] < num]
        x = after[0][2] if after else (before[-1][3] if before else x_beg)
        out.append((num, (lo + hi) / 2.0, x, x))
    return out


def init_knots(pieces: list, lays: list, x_beg: float, x_end: float,
               min_width: float) -> list:
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
    return order_knots(knots, x_beg, x_end, min_width)


def order_knots(knots: list, x_beg: float, x_end: float,
                min_width: float) -> list:
    """Границы строго по возрастанию, с зазором.

    Зазор нужен только чтобы они не слиплись: разносить их равномерно по всему
    диапазону нельзя — спуск потом не вытащит первую границу с сотен метров."""
    n = len(knots)
    if not n:
        return []
    out = list(knots)
    gap = min(min_width, (x_end - x_beg) / (2.0 * (n + 1)))
    for i in range(n):
        lo = x_beg + gap * (i + 1)
        if i:
            lo = max(lo, out[i - 1] + gap)
        out[i] = min(max(out[i], lo), x_end - gap * (n - i))
    return out


knot_eps = 1e-3     # чтобы схлопнувшийся слой не делил на ноль


def knot_limits(pieces: list, lays: list, x_beg: float,
                x_end: float) -> list:
    """Коридор [от, до] для каждой границы слоёв.

    Кусок годографа, скорость которого лежит внутри диапазона слоя, достаётся
    этому слою целиком. Иначе в окно второго слоя попадают удаления, где в
    первых вступлениях ещё первый слой, и пикировка по такому окну соберёт не ту
    волну. Куски со скоростью в зазоре между диапазонами не принадлежат никому —
    внутри них граница и ставится, там же работает интерполяция.

    При смежных диапазонах (2200 — потолок второго слоя и низ третьего) зазоров
    нет, и коридор схлопывается до стыка кусков: граница встаёт ровно туда, где
    скорость перешла порог."""
    owned = []
    for x1, x2, t0, v in pieces:
        num = None
        for lay in lays:
            if lay[1] <= v <= lay[2]:
                num = lay[0]
                break
        owned.append((max(x1, x_beg), min(x2, x_end), num))

    limits = []
    for i in range(len(lays) - 1):
        a, b = x_beg, x_end
        for x1, x2, num in owned:
            if num is None or x2 <= x1:
                continue
            if num <= lays[i][0]:
                a = max(a, x2)
            elif num >= lays[i + 1][0]:
                b = min(b, x1)
        limits.append((a, b))

    out = []                        # по возрастанию и без нулевой ширины слоя
    prev = x_beg
    for i, (a, b) in enumerate(limits):
        far = x_end - knot_eps * (len(limits) - i)
        a = min(max(a, prev + knot_eps), far)
        b = min(max(b, a), far)
        out.append((a, b))
        prev = a
    return out


def clamp_knots(knots: list, limits: list, x_end: float) -> list:
    """Границы внутрь коридоров и строго по возрастанию.

    Коридоры соседних границ могут наложиться, если у слоя между ними нет своих
    кусков, — тогда порядок важнее коридора, иначе слой выйдет отрицательной
    ширины."""
    out = []
    for k, (a, b) in zip(knots, limits):
        k = min(max(k, a), b)
        if out:
            k = max(k, out[-1] + knot_eps)
        out.append(min(k, x_end - knot_eps))
    return out


def line_fit(curve: list, a: float, b: float) -> tuple:
    """МНК-прямая t = A + B*x по куску годографа [a, b], вес 1/x — тот же, что
    в misfit. Интегралы берём точно по изломам годографа, без дискретизации."""
    s0, s1, s2 = math.log(b / a), b - a, (b * b - a * a) / 2.0
    r0 = r1 = 0.0
    edges = sorted({a, b} | {ln[0] for ln in curve if a < ln[0] < b})
    for u, v in zip(edges, edges[1:]):
        c, d = pick(curve, (u + v) / 2.0)[1:]
        r0 += c * math.log(v / u) + d * (v - u)
        r1 += c * (v - u) + d * (v * v - u * u) / 2.0
    det = s0 * s2 - s1 * s1
    if abs(det) < 1e-12:
        return 0.0, s1 / max(s2, 1e-12)
    return (r0 * s2 - r1 * s1) / det, (s0 * r1 - s1 * r0) / det


def window_vels(curve: list, bounds: list) -> tuple:
    """Скорости слоёв по их собственным окнам: (скорости, прямые).

    Скорость слоя считается МНК по его окну, а не берётся из общей ломаной.
    Границы заданы данными и подбору не подчиняются, поэтому ломаная, вытягивая
    общую невязку, перекашивала скорости: на проверке второй слой выходил
    1299 м/с там, где кусок годографа даёт 2104."""
    lines, vels = [], []
    for a, b in zip(bounds, bounds[1:]):
        ca, cb = line_fit(curve, a, b)
        lines.append((b, ca, cb))
        vels.append(1000.0 / cb if cb > 1e-9 else 0.0)
    return vels, lines


def threshold_x(pieces: list, thr: float, x_beg: float, x_end: float) -> float:
    """Удаление, на котором кажущаяся скорость пересекает порог thr.

    Скорость куска относится ко всему куску, поэтому смена скорости размазана в
    переход вокруг общей границы двух кусков, и порог ищется внутри перехода.
    Ширина перехода — по более короткому из двух кусков: последний кусок в f1
    всегда тянется до дальнего удаления, и интерполяция между серединами уносила
    границу на его середину (на проверке 80 м превращались в 840).

    Кажущаяся скорость растёт не строго, поэтому берём первое пересечение."""
    ends = []
    for x1, x2, t0, v in pieces:
        a, b = max(x1, x_beg), min(x2, x_end)
        if b > a:
            ends.append((a, b, v))
    if not ends or ends[0][2] >= thr:
        return x_beg
    for (a1, b1, v1), (a2, b2, v2) in zip(ends, ends[1:]):
        if v2 >= thr > v1:
            half = min(b1 - a1, b2 - a2) / 2.0
            f = (thr - v1) / (v2 - v1)
            return min(max(b1 - half + f * 2.0 * half, x_beg), x_end)
    return x_end


def fit_threshold(pieces: list, lays: list, x_beg: float, x_end: float,
                  min_width: float, limits: list) -> tuple:
    """Границы по порогам скорости. Возвращает (границы, скорости, СКО).

    Порог между соседними слоями — середина зазора между их диапазонами (для
    смежных диапазонов это их общая граница). Скорость слоя считается МНК по его
    окну и в диапазон не зажимается: окно уже определено порогом, и подгонять
    под него ещё и скорость значило бы врать в отчёте."""
    knots = [threshold_x(pieces, (lays[i][2] + lays[i + 1][1]) / 2.0, x_beg, x_end)
             for i in range(len(lays) - 1)]
    knots = clamp_knots(knots, limits, x_end)
    curve = curve_lines(pieces)
    vels, lines = window_vels(curve, [x_beg] + knots + [x_end])
    return knots, vels, misfit(curve, lines, x_beg, x_end)


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
        if k <= n:                          # k — время в узле
            q2 = list(p)                    # сдвиг хвоста: время узла и всех
            for j in range(k, n + 1):       # следующих. Меняет скорость ровно
                q2[j] += d                  # одного слоя, тогда как одиночный
            out.append(q2)                  # сдвиг узла ломает сразу два
        else:                               # k — граница слоя, узел k-n
            j = k - n - 1
            for b in (lines[j][2], lines[j + 1][2]):
                q2 = list(p)
                q2[k] += d
                q2[j + 1] += b * d
                out.append(q2)
    return out


def fit(pieces: list, lays: list, x_beg: float, x_end: float,
        min_width: float, limits: list) -> tuple:
    """Подбор ломаной покоординатным спуском. Возвращает (границы, скорости, СКО).

    Параметры МНК: времена в узлах и удаления границ слоёв. Скорость каждой
    прямой зажата в диапазон своего слоя, границы — в свои коридоры (limits) и
    строго по возрастанию. Ломаная нужна только чтобы поставить границы; сами
    скорости считаются потом по окнам, см. window_vels."""
    n = len(lays)
    curve = curve_lines(pieces)
    knots = clamp_knots(init_knots(pieces, lays, x_beg, x_end, min_width),
                        limits, x_end)
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
        for i, (a, b) in enumerate(limits):
            if not a <= xq[i + 1] <= b:
                return False
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
    knots = list(p[n + 1:])
    vels, lines = window_vels(curve, [x_beg] + knots + [x_end])
    return knots, vels, misfit(curve, lines, x_beg, x_end)


def build(pieces: list, cfg: Config) -> tuple:
    """(слои, СКО) для одного ПВ. Слой — (номер, V, удаление от, удаление до)."""
    lays = used_layers(pieces, cfg.layers, cfg.missing)
    x_beg = max(pieces[0][0], 0.1)      # вес 1/x в невязке нуля не терпит
    x_end = min(max(pc[1] for pc in pieces), cfg.max_offset)
    if not lays or x_end - x_beg < cfg.min_layer_width:
        return [], None
    if len(lays) == 1:
        model, rms = [(lays[0][0], pieces[0][3], x_beg, x_end)], 0.0
    else:
        method = fit_threshold if cfg.method == 'threshold' else fit
        limits = knot_limits(pieces, lays, x_beg, x_end)
        knots, vels, rms = method(pieces, lays, x_beg, x_end,
                                  cfg.min_layer_width, limits)
        bounds = [x_beg] + list(knots) + [x_end]
        model = [(lays[i][0], vels[i], bounds[i], bounds[i + 1])
                 for i in range(len(lays))]
    if cfg.missing == 'degenerate' and len(model) < len(cfg.layers):
        model = pad_missing(model, cfg.layers, x_beg, x_end)
    return model, rms


def round_window(x_from: float, x_to: float, step: int, mode: str) -> tuple:
    """Окно слоя на сетку шага step.

    'near' — обе границы к ближайшему узлу. Соседние слои делят одну границу и
    округляют её одинаково, поэтому окна остаются встык.
    'in'   — окно сжимается внутрь: минимум вверх, максимум вниз. В окно тогда
    не попадают трассы у самого перехода, где вступление уже принадлежит
    соседнему слою, — ценой зазора между окнами соседей.

    Сжимать можно не всегда: на узком слое минимум перескочит максимум. Для
    такого окна берётся обычное округление — пустое окно хуже, чем окно с
    краевыми трассами."""
    def near(v):
        return int(math.floor(v / step + 0.5)) * step

    if mode == 'in':
        lo = int(math.ceil(x_from / step)) * step
        hi = int(math.floor(x_to / step)) * step
        if hi > lo:
            return lo, hi
    lo, hi = near(x_from), near(x_to)
    return lo, max(hi, lo)


def write_blocks(path: Path, rows: list, first_layer: int, fmt,
                 lays: list) -> int:
    """Блок на слой, номер слоя только в первой строке своего блока."""
    written = 0
    with open(path, 'w') as f:
        for lay_def in lays:
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


def run(cfg: Config, log=print) -> None:
    """Весь счёт: прочитать, построить модели, записать оба файла."""
    err = check_layers(cfg.layers)
    if err:
        log(err)
        return

    path_1 = Path(cfg.f1_path).absolute()
    path_2 = Path(cfg.f2_path).absolute()
    for p in (path_1, path_2):
        if not p.exists():
            log(f'Нет файла: {p}')
            return

    data = read_f1(path_1, cfg, log)
    coords = read_f2(path_2, cfg, log)
    log(f'f1: ПВ {len(data)}, f2: точек {len(coords)}')

    rows = []           # (ПВ, X, Y, (слой, V, от, до)) — по строке на слой
    missed, empty, pinned, split, outside = [], [], [], [], []
    thin, hollow, rough = [], [], []
    bands = {lay[0]: lay for lay in cfg.layers}
    # край диапазона, за которым сразу начинается соседний слой, расширять
    # некуда: упор в него значит лишь, что скорость села на границу между
    # слоями, и звать это узким диапазоном нельзя
    shared = set()
    for a, b in zip(cfg.layers, cfg.layers[1:]):
        if abs(a[2] - b[1]) < 1e-9:
            shared.add((a[0], 'hi'))
            shared.add((b[0], 'lo'))
    for pv, pieces in data:
        xy = coords.get(pv)
        if xy is None:
            missed.append(pv)
            continue
        model, rms = build(pieces, cfg)
        if not model:
            empty.append(pv)
            continue
        if rms is not None and rms > cfg.bad_rms:
            rough.append((rms, pv))
        for lay in model:
            num, v, x_from, x_to = lay
            band = bands[num]
            if x_to - x_from <= 0.0:        # слой без вступлений, скорость
                hollow.append(pv)           # взята серединой диапазона
            else:
                if v < band[1] or v > band[2]:
                    outside.append(pv)
                elif abs(v - band[1]) < 1.0:
                    (split if (num, 'lo') in shared else pinned).append(pv)
                elif abs(v - band[2]) < 1.0:
                    (split if (num, 'hi') in shared else pinned).append(pv)
                if x_to - x_from < cfg.min_layer_width:
                    thin.append(pv)
            rows.append((pv, xy[0], xy[1], lay))

    parent = Path(cfg.out_dir).absolute() if cfg.out_dir else path_1.parent

    # окно слоя не может начинаться ближе ближнего удаления съёмки: у ПВ без
    # первого слоя модель стартует с 1 м из первой строки f1 и после округления
    # вниз давала 0
    off_rows, squeezed = [], []
    for pv, x, y, lay in rows:
        if lay[0] < 2:                  # первый слой в удаления не пишем
            continue
        lo, hi = round_window(lay[2], lay[3], cfg.round_step, cfg.round_mode)
        lo = max(lo, cfg.min_offset)    # окно целиком ближе ближнего удаления
        hi = max(hi, lo)
        if hi == lo and lay[3] - lay[2] > 0.0:
            squeezed.append(pv)
        off_rows.append((pv, x, y, (lay[0], lo, hi)))

    path_off = parent / f'{path_1.stem}_offset.txt'
    n_off = write_blocks(
        path_off, off_rows, 2,
        lambda x, y, lay: '{:.1f}\t{:.1f}\t{}\t{}'.format(x, y, lay[1], lay[2]),
        cfg.layers)
    log(f'удаления: записано {n_off} строк -> {path_off}')

    path_spd = parent / f'{path_1.stem}_speed.txt'
    n_spd = write_blocks(
        path_spd, rows, 1,
        lambda x, y, lay: '{:.1f}\t{:.1f}\t{:.1f}'.format(x, y, lay[1]),
        cfg.layers)
    log(f'скорости: записано {n_spd} строк -> {path_spd}')

    if missed:
        log(f'Нет координат для {len(missed)} ПВ: {", ".join(missed[:20])}'
            f'{" ..." if len(missed) > 20 else ""}')
    if empty:
        log(f'Не из чего строить модель, {len(empty)} ПВ: {", ".join(empty[:20])}')
    if pinned:
        uniq = sorted(set(pinned))
        log(f'Скорость упёрлась в край диапазона на {len(uniq)} ПВ — '
            f'диапазоны стоит расширить: {", ".join(uniq[:20])}'
            f'{" ..." if len(uniq) > 20 else ""}')
    if outside:
        uniq = sorted(set(outside))
        log(f'Скорость слоя вышла за свой диапазон на {len(uniq)} ПВ — порог '
            f'провёл границу там, где скорость слою уже не отвечает: '
            f'{", ".join(uniq[:20])}{" ..." if len(uniq) > 20 else ""}')
    if split:
        uniq = sorted(set(split))
        log(f'Скорость села на границу между слоями на {len(uniq)} ПВ — там '
            f'годограф не делится на два слоя однозначно: {", ".join(uniq[:20])}'
            f'{" ..." if len(uniq) > 20 else ""}')
    if thin:
        uniq = sorted(set(thin))
        log(f'Слой уже {cfg.min_layer_width:.0f} м на {len(uniq)} ПВ: '
            f'{", ".join(uniq[:20])}')
    if squeezed:
        uniq = sorted(set(squeezed))
        log(f'Окно слоя схлопнулось при округлении на {len(uniq)} ПВ — слой '
            f'уже шага округления: {", ".join(uniq[:20])}'
            f'{" ..." if len(uniq) > 20 else ""}')
    if hollow:
        uniq = sorted(set(hollow))
        log(f'Слоя нет в данных, вписан вырожденным окном на {len(uniq)} ПВ: '
            f'{", ".join(uniq[:20])}{" ..." if len(uniq) > 20 else ""}')
    if rough:
        rough.sort(reverse=True)
        log(f'Невязка модели больше {cfg.bad_rms:.0f} мс на {len(rough)} ПВ, '
            'худшие: ' + ', '.join(f'{pv} ({r:.1f} мс)' for r, pv in rough[:10]))


class Worker(QObject):
    """Счёт в отдельном потоке: на реальном массиве это минуты, в главном потоке
    окно бы всё это время висело."""

    message = Signal(str)
    finished = Signal()

    def __init__(self, cfg: Config):
        super().__init__()
        self.cfg = cfg

    @Slot()
    def work(self):
        try:
            run(self.cfg, self.message.emit)
        except Exception as e:
            self.message.emit(f'Сорвалось: {e.__class__.__name__}: {e}')
        self.finished.emit()


def spin(lo: int, hi: int, value: int) -> QSpinBox:
    box = QSpinBox()
    box.setRange(lo, hi)
    box.setValue(value)
    return box


def dspin(lo: float, hi: float, value: float, step: float, dec: int = 1):
    box = QDoubleSpinBox()
    box.setRange(lo, hi)
    box.setDecimals(dec)
    box.setSingleStep(step)
    box.setValue(value)
    return box


class Window(QWidget):
    """Окно настроек. Значения по умолчанию — из Config, между запусками
    сохраняются в QSettings: пути к рабочим дискам длинные, набирать их заново
    на каждой партии незачем."""

    def __init__(self):
        super().__init__()
        self.cfg = Config()
        self.thread = None
        self.worker = None
        self.build_ui()
        self.load_settings()

    # --- сборка окна -----------------------------------------------------

    def build_ui(self):
        cfg = self.cfg
        self.setWindowTitle('LMO -> модель ВЧР: удаления и скорости слоёв')

        self.ed_f1 = QLineEdit(cfg.f1_path)
        self.ed_f2 = QLineEdit(cfg.f2_path)
        self.ed_out = QLineEdit(cfg.out_dir)
        self.ed_out.setPlaceholderText('пусто — класть рядом с файлом LMO')

        files = QFormLayout()
        files.addRow('Файл LMO', self.with_browse(self.ed_f1, self.pick_f1))
        files.addRow('Файл SPS', self.with_browse(self.ed_f2, self.pick_f2))
        files.addRow('Каталог вывода', self.with_browse(self.ed_out, self.pick_out))
        box_files = QGroupBox('Файлы')
        box_files.setLayout(files)

        self.sp_pv = spin(0, 50, cfg.pv_col)
        self.sp_x1 = spin(0, 50, cfg.x1_col)
        self.sp_x2 = spin(0, 50, cfg.x2_col)
        self.sp_t0 = spin(0, 50, cfg.t0_col)
        self.sp_v = spin(0, 50, cfg.v_col)
        cols = QFormLayout()
        cols.addRow('Номер ПВ', self.sp_pv)
        cols.addRow('Мин. удаление', self.sp_x1)
        cols.addRow('Макс. удаление', self.sp_x2)
        cols.addRow('Интерсепт, мс', self.sp_t0)
        cols.addRow('Скорость, м/с', self.sp_v)
        box_cols = QGroupBox('Колонки в файле LMO (с нуля)')
        box_cols.setLayout(cols)

        self.sps_spins = {}
        grid = QGridLayout()
        grid.addWidget(QLabel('с'), 0, 1)
        grid.addWidget(QLabel('по'), 0, 2)
        for row, (key, title) in enumerate(
                (('sps_line_pos', 'Линия ПВ'), ('sps_point_pos', 'Точка ПВ'),
                 ('sps_x_pos', 'X'), ('sps_y_pos', 'Y')), start=1):
            lo, hi = getattr(cfg, key)
            a, b = spin(1, 500, lo), spin(1, 500, hi)
            self.sps_spins[key] = (a, b)
            grid.addWidget(QLabel(title), row, 0)
            grid.addWidget(a, row, 1)
            grid.addWidget(b, row, 2)
        box_sps = QGroupBox('Позиции в SPS (с единицы, границы включительно)')
        box_sps.setLayout(grid)

        self.tbl = QTableWidget(0, 3)
        self.tbl.setHorizontalHeaderLabels(['Слой', 'V мин, м/с', 'V макс, м/с'])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl.verticalHeader().hide()
        self.set_layers(cfg.layers)
        btn_add = QPushButton('Добавить слой')
        btn_add.clicked.connect(self.add_layer)
        btn_del = QPushButton('Удалить слой')
        btn_del.clicked.connect(self.del_layer)
        lay_btns = QHBoxLayout()
        lay_btns.addWidget(btn_add)
        lay_btns.addWidget(btn_del)
        lay_btns.addStretch()
        box_lay_inner = QVBoxLayout()
        box_lay_inner.addWidget(self.tbl)
        box_lay_inner.addLayout(lay_btns)
        box_lay = QGroupBox('Слои модели: диапазоны скоростей')
        box_lay.setLayout(box_lay_inner)

        self.sp_round = spin(1, 1000, cfg.round_step)
        self.cb_round = QComboBox()
        for title, key in (('обычное', 'near'),
                           ('внутрь: мин вверх, макс вниз', 'in')):
            self.cb_round.addItem(title, key)
        self.cb_round.setCurrentIndex(
            max(0, self.cb_round.findData(cfg.round_mode)))
        self.sp_min = spin(0, 100000, cfg.min_offset)
        self.sp_max = dspin(10.0, 1e6, cfg.max_offset, 100.0)
        self.sp_width = dspin(0.0, 1e4, cfg.min_layer_width, 1.0)
        self.sp_rms = dspin(0.0, 1e4, cfg.bad_rms, 1.0)
        self.cb_method = QComboBox()
        for title, key in (('МНК, ломаная по слоям', 'lsq'),
                           ('порог по скорости с интерполяцией', 'threshold')):
            self.cb_method.addItem(title, key)
        self.cb_method.setCurrentIndex(
            max(0, self.cb_method.findData(cfg.method)))
        self.cb_missing = QComboBox()
        for title, key in (('вырожденным окном', 'degenerate'),
                           ('подбирать все слои', 'all'),
                           ('пропускать', 'skip')):
            self.cb_missing.addItem(title, key)
        self.cb_missing.setCurrentIndex(
            max(0, self.cb_missing.findData(cfg.missing)))
        calc = QFormLayout()
        calc.addRow('Границы слоёв считать', self.cb_method)
        calc.addRow('Округление удалений до, м', self.sp_round)
        calc.addRow('Округление удалений', self.cb_round)
        calc.addRow('Ближнее удаление съёмки, м', self.sp_min)
        calc.addRow('Дальнее удаление съёмки, м', self.sp_max)
        calc.addRow('Порог тонкого слоя, м', self.sp_width)
        calc.addRow('Порог большой невязки, мс', self.sp_rms)
        calc.addRow('Слой, которого нет в данных', self.cb_missing)
        box_calc = QGroupBox('Счёт')
        box_calc.setLayout(calc)

        self.btn_run = QPushButton('Посчитать')
        self.btn_run.clicked.connect(self.start)
        self.chk_clear = QCheckBox('Чистить журнал перед запуском')
        self.chk_clear.setChecked(True)
        run_row = QHBoxLayout()
        run_row.addWidget(self.btn_run)
        run_row.addWidget(self.chk_clear)
        run_row.addStretch()

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(180)

        left = QVBoxLayout()
        left.addWidget(box_cols)
        left.addWidget(box_sps)
        left.addStretch()
        right = QVBoxLayout()
        right.addWidget(box_lay)
        right.addWidget(box_calc)
        middle = QHBoxLayout()
        middle.addLayout(left)
        middle.addLayout(right)

        root = QVBoxLayout(self)
        root.addWidget(box_files)
        root.addLayout(middle)
        root.addLayout(run_row)
        root.addWidget(QLabel('Журнал'))
        root.addWidget(self.log_view)
        self.resize(880, 720)

    def with_browse(self, edit: QLineEdit, slot) -> QWidget:
        btn = QPushButton('Обзор…')
        btn.clicked.connect(slot)
        box = QHBoxLayout()
        box.setContentsMargins(0, 0, 0, 0)
        box.addWidget(edit)
        box.addWidget(btn)
        holder = QWidget()
        holder.setLayout(box)
        return holder

    # --- таблица слоёв ---------------------------------------------------

    def renumber(self):
        """Номер слоя — это его место сверху вниз, руками он не правится.

        Пока номер был обычной ячейкой, удаление строки из середины оставляло
        дыру: слои шли 1, 2, 4, и в файлы уходил слой с номером 4, хотя слоёв
        было три."""
        for row in range(self.tbl.rowCount()):
            item = QTableWidgetItem(str(row + 1))
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.tbl.setItem(row, 0, item)

    def set_layers(self, lays: list):
        self.tbl.setRowCount(len(lays))
        for row, (num, lo, hi) in enumerate(lays):
            for col, val in ((1, lo), (2, hi)):
                item = QTableWidgetItem(f'{val:.0f}')
                item.setTextAlignment(Qt.AlignCenter)
                self.tbl.setItem(row, col, item)
        self.renumber()

    def get_layers(self) -> list:
        lays = []
        for row in range(self.tbl.rowCount()):
            vals = []
            for col in (1, 2):
                item = self.tbl.item(row, col)
                vals.append(item.text().strip() if item else '')
            try:
                lays.append((row + 1, float(vals[0]), float(vals[1])))
            except ValueError:
                raise ValueError(f'Строка слоёв {row + 1}: не число')
        return lays

    def add_layer(self):
        row = self.tbl.rowCount()
        self.tbl.insertRow(row)
        for col in (1, 2):
            item = QTableWidgetItem('0')
            item.setTextAlignment(Qt.AlignCenter)
            self.tbl.setItem(row, col, item)
        self.renumber()

    def del_layer(self):
        row = self.tbl.currentRow()
        if row < 0:
            row = self.tbl.rowCount() - 1
        if row >= 0:
            self.tbl.removeRow(row)
            self.renumber()

    # --- выбор файлов ----------------------------------------------------

    def pick_f1(self):
        name, _ = QFileDialog.getOpenFileName(
            self, 'Файл LMO', self.ed_f1.text(), 'Текст (*.txt);;Все файлы (*)')
        if name:
            self.ed_f1.setText(name)

    def pick_f2(self):
        name, _ = QFileDialog.getOpenFileName(
            self, 'Файл SPS', self.ed_f2.text(), 'SPS (*.sps *.s01);;Все файлы (*)')
        if name:
            self.ed_f2.setText(name)

    def pick_out(self):
        name = QFileDialog.getExistingDirectory(
            self, 'Каталог вывода', self.ed_out.text() or self.ed_f1.text())
        if name:
            self.ed_out.setText(name)

    # --- настройки между запусками ---------------------------------------

    def load_settings(self):
        s = QSettings('scripts_for_work', 'lmoToXY')
        geometry = s.value('geometry')       # до раннего выхода: размеры окна
        if geometry is not None:             # помнятся и после первого запуска,
            self.restoreGeometry(geometry)   # когда путей ещё не сохранено
        if not s.value('f1_path'):
            return
        self.ed_f1.setText(s.value('f1_path', self.ed_f1.text()))
        self.ed_f2.setText(s.value('f2_path', self.ed_f2.text()))
        self.ed_out.setText(s.value('out_dir', ''))
        for key, box in (('pv_col', self.sp_pv), ('x1_col', self.sp_x1),
                         ('x2_col', self.sp_x2), ('t0_col', self.sp_t0),
                         ('v_col', self.sp_v), ('round_step', self.sp_round),
                         ('min_offset', self.sp_min)):
            box.setValue(int(s.value(key, box.value())))
        for key, box in (('max_offset', self.sp_max),
                         ('min_layer_width', self.sp_width),
                         ('bad_rms', self.sp_rms)):
            box.setValue(float(s.value(key, box.value())))
        for key, (a, b) in self.sps_spins.items():
            a.setValue(int(s.value(key + '_lo', a.value())))
            b.setValue(int(s.value(key + '_hi', b.value())))
        for key, box in (('round_mode', self.cb_round),
                         ('method', self.cb_method), ('missing', self.cb_missing)):
            pos = box.findData(s.value(key, box.currentData()))
            if pos >= 0:
                box.setCurrentIndex(pos)
        raw = s.value('layers', '')
        if raw:
            lays = [tuple(float(v) for v in part.split(','))
                    for part in raw.split(';') if part]
            self.set_layers([(int(n), lo, hi) for n, lo, hi in lays])

    def save_settings(self):
        s = QSettings('scripts_for_work', 'lmoToXY')
        s.setValue('geometry', self.saveGeometry())
        s.setValue('f1_path', self.ed_f1.text())
        s.setValue('f2_path', self.ed_f2.text())
        s.setValue('out_dir', self.ed_out.text())
        for key, box in (('pv_col', self.sp_pv), ('x1_col', self.sp_x1),
                         ('x2_col', self.sp_x2), ('t0_col', self.sp_t0),
                         ('v_col', self.sp_v), ('round_step', self.sp_round),
                         ('min_offset', self.sp_min),
                         ('max_offset', self.sp_max),
                         ('min_layer_width', self.sp_width),
                         ('bad_rms', self.sp_rms)):
            s.setValue(key, box.value())
        for key, (a, b) in self.sps_spins.items():
            s.setValue(key + '_lo', a.value())
            s.setValue(key + '_hi', b.value())
        s.setValue('round_mode', self.cb_round.currentData())
        s.setValue('method', self.cb_method.currentData())
        s.setValue('missing', self.cb_missing.currentData())
        try:
            lays = self.get_layers()
        except ValueError:
            return
        s.setValue('layers', ';'.join(f'{n},{lo},{hi}' for n, lo, hi in lays))

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

    # --- запуск ----------------------------------------------------------

    def collect(self) -> Config:
        cfg = Config()
        cfg.f1_path = self.ed_f1.text().strip()
        cfg.f2_path = self.ed_f2.text().strip()
        cfg.out_dir = self.ed_out.text().strip()
        cfg.pv_col = self.sp_pv.value()
        cfg.x1_col = self.sp_x1.value()
        cfg.x2_col = self.sp_x2.value()
        cfg.t0_col = self.sp_t0.value()
        cfg.v_col = self.sp_v.value()
        cfg.round_step = self.sp_round.value()
        cfg.min_offset = self.sp_min.value()
        cfg.max_offset = self.sp_max.value()
        cfg.min_layer_width = self.sp_width.value()
        cfg.bad_rms = self.sp_rms.value()
        cfg.round_mode = self.cb_round.currentData()
        cfg.method = self.cb_method.currentData()
        cfg.missing = self.cb_missing.currentData()
        for key, (a, b) in self.sps_spins.items():
            setattr(cfg, key, (a.value(), b.value()))
        cfg.layers = self.get_layers()
        return cfg

    @Slot(str)
    def append(self, text: str):
        self.log_view.appendPlainText(text)

    def start(self):
        try:
            cfg = self.collect()
        except ValueError as e:
            QMessageBox.warning(self, 'Настройки', str(e))
            return
        err = check_layers(cfg.layers)
        if err:
            QMessageBox.warning(self, 'Слои', err)
            return
        if self.chk_clear.isChecked():
            self.log_view.clear()
        self.save_settings()
        self.btn_run.setEnabled(False)
        self.append('Считаю…')

        self.thread = QThread(self)
        self.worker = Worker(cfg)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.work)
        self.worker.message.connect(self.append)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.done)
        self.thread.start()

    @Slot()
    def done(self):
        self.append('Готово')
        self.btn_run.setEnabled(True)
        self.worker = None
        self.thread = None


def main():
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
