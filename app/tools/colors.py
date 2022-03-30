# tools for color generation. used for arrow color
import numpy as np

def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

def rgb_to_hex(rgb):
    rgb = (int(rgb[0]), int(rgb[1]), int(rgb[2]))
    return '#%02x%02x%02x' % rgb

def lighter(color, percent):
    color = np.array(color)
    white = np.array([255, 255, 255])
    vector = white - color
    return color + vector * percent

def gen_outline_color(base, percent):
    rgb = hex_to_rgb(base)
    new = lighter(rgb, percent)
    return rgb_to_hex(new)
