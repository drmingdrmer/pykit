#!/usr/bin/env python2
# coding: utf-8

from pykit import rangeset

class NN(str):
    def __str__(self):
        return 'null'

class Ractangle(list):

    def __init__(self, xrng, yrng, val=None):
        xrng = rangeset.Range(xrng[0], xrng[1])
        yrng = rangeset.Range(yrng[0], yrng[1])

        super(Ractangle, self).__init__([xrng, yrng, val])

    def dup(self):
        return self.__class__(*self)

    def intersect(self, other):
        x, y, val = self
        u, v = other[:2]

        xx = x.intersect(u)
        if xx is None:
            return None

        yy = y.intersect(v)
        if yy is None:
            return None

        return self.__class__(xx, yy, val)

    def complement(self):
        clz = self.__class__

        x, y, val = self

        x0 = clz([None, x[0]], [None, None], val)
        x1 = clz([x[1], None], [None, None], val)
        y0 = clz(x, [None, y[0]], val)
        y1 = clz(x, [y[1], None], val)

        return [x0, x1, y0, y1]

    def substract(self, other):

        x0, x1, y0, y1 = self.complement()

        x0 = x0.intersect(other)
        x1 = x1.intersect(other)
        y0 = y0.intersect(other)
        y1 = y1.intersect(other)

        return [x0, x1, y0, y1]

    def union(self, other):
        others = other.substract(self)

        return [self.dup()] + [x for x in others if x is not None]

    def points(self, symbol=None):

        if symbol is None:
            symbol = str(self[2])[0]

        points = {}

        xrng, yrng, val = self
        for x in range(xrng[0], xrng[1]+1):
            x = int(x)
            points[(x, int(yrng[0]))] = 1
            points[(x, int(yrng[1]))] = 1

        for y in range(yrng[0], yrng[1]+1):
            y = int(y)
            points[(int(xrng[0]), y)] = 1
            points[(int(xrng[1]), y)] = 1

        ps = []
        for k in points:
            ps.append(k + (symbol, ))
        return ps

    def draw(self, w=40, h=10):
        points = self.points()

        xs, ys = zip(*points)
        x0, x1 = min(xs), max(xs)
        y0, y1 = min(ys), max(ys)

        canvas = [['-'] * (w+1) for _ in range(0, h+1)]

        for x, y in points:
            x = int(float(x)/x1*w)
            y = int(float(y)/y1*h)
            canvas[y][x] = 'x'

        canvas = [''.join(x) for x in canvas]
        canvas.reverse()

        return canvas


def draw(rects, w=40, h=10):
    symbols = 'abcdefghijklmnopqrstuvwxyz'
    points = []
    for i, r in enumerate(rects):
        points.extend(r.points(symbol=symbols[i]))

    return draw_points(points, w=w, h=h)


def draw_points(points, w=40, h=10):

    xs, ys, _ = zip(*points)
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)

    canvas = [['-'] * (w+1) for _ in range(0, h+1)]

    for x, y, symbol in points:
        x = int(float(x)/x1*w)
        y = int(float(y)/y1*h)
        canvas[y][x] = symbol

    canvas = [''.join(x) for x in canvas]
    canvas.reverse()

    return canvas
