import argparse
import math
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib

matplotlib.use('Agg')

import matplotlib.font_manager as font_manager
import matplotlib.patches as patches
import matplotlib.pyplot as plt


def parse_args():
    parser = argparse.ArgumentParser(
        description='Render simple DrawIO diagrams to PDF and PNG.')
    parser.add_argument('inputs', nargs='+', type=Path)
    return parser.parse_args()


def style_dict(style):
    values = {}
    for item in (style or '').split(';'):
        if '=' in item:
            key, value = item.split('=', 1)
            values[key] = value
    return values


def line_rectangle_intersection(center, target, rect):
    x, y, width, height = rect
    cx, cy = center
    dx = target[0] - cx
    dy = target[1] - cy
    if dx == 0 and dy == 0:
        return center
    candidates = []
    if dx != 0:
        for boundary in (x, x + width):
            t = (boundary - cx) / dx
            yy = cy + t * dy
            if t >= 0 and y <= yy <= y + height:
                candidates.append((t, boundary, yy))
    if dy != 0:
        for boundary in (y, y + height):
            t = (boundary - cy) / dy
            xx = cx + t * dx
            if t >= 0 and x <= xx <= x + width:
                candidates.append((t, xx, boundary))
    if not candidates:
        return center
    _, px, py = min(candidates, key=lambda item: item[0])
    return px, py


def render(input_path):
    tree = ET.parse(input_path)
    model = tree.find('.//mxGraphModel')
    width = float(model.attrib.get('pageWidth', 1200))
    height = float(model.attrib.get('pageHeight', 600))
    cells = {
        cell.attrib['id']: cell
        for cell in tree.findall('.//mxCell')
        if 'id' in cell.attrib
    }
    vertices = {}
    fig, axis = plt.subplots(
        figsize=(width / 120, height / 120),
        constrained_layout=True)
    axis.set_xlim(0, width)
    axis.set_ylim(height, 0)
    axis.axis('off')
    axis.set_facecolor('white')

    for identifier, cell in cells.items():
        if cell.attrib.get('vertex') != '1':
            continue
        geometry = cell.find('mxGeometry')
        if geometry is None:
            continue
        x = float(geometry.attrib.get('x', 0))
        y = float(geometry.attrib.get('y', 0))
        box_width = float(geometry.attrib.get('width', 0))
        box_height = float(geometry.attrib.get('height', 0))
        vertices[identifier] = (x, y, box_width, box_height)
        style = style_dict(cell.attrib.get('style'))
        value = (cell.attrib.get('value') or '').replace('<br>', '\n')
        fill = style.get('fillColor')
        stroke = style.get('strokeColor')
        font_size = float(style.get('fontSize', 13))
        is_text = 'text' in (cell.attrib.get('style') or '') and not fill
        if not is_text:
            patch = patches.FancyBboxPatch(
                (x, y), box_width, box_height,
                boxstyle='round,pad=0,rounding_size=8',
                linewidth=1.2,
                edgecolor=stroke or '#555555',
                facecolor=fill or '#FFFFFF')
            axis.add_patch(patch)
        axis.text(
            x + box_width / 2,
            y + box_height / 2,
            value,
            ha='center',
            va='center',
            fontsize=min(14, max(7, font_size * 0.72)),
            fontweight='bold' if style.get('fontStyle') == '1' else 'normal',
            color='#202428',
            linespacing=1.25)

    for cell in cells.values():
        if cell.attrib.get('edge') != '1':
            continue
        source = vertices.get(cell.attrib.get('source'))
        target = vertices.get(cell.attrib.get('target'))
        if not source or not target:
            continue
        source_center = (
            source[0] + source[2] / 2,
            source[1] + source[3] / 2)
        target_center = (
            target[0] + target[2] / 2,
            target[1] + target[3] / 2)
        start = line_rectangle_intersection(
            source_center, target_center, source)
        end = line_rectangle_intersection(
            target_center, source_center, target)
        axis.annotate(
            '',
            xy=end,
            xytext=start,
            arrowprops={
                'arrowstyle': '-|>',
                'color': '#4A5055',
                'linewidth': 1.1,
                'shrinkA': 0,
                'shrinkB': 0,
            })

    output_pdf = input_path.with_suffix('.pdf')
    output_png = input_path.with_suffix('.png')
    fig.savefig(output_pdf)
    fig.savefig(output_png)
    plt.close(fig)
    print(f'Rendered {input_path} -> {output_pdf.name}')


def main():
    args = parse_args()
    font_path = Path('C:/Windows/Fonts/msyh.ttc')
    if font_path.exists():
        font_manager.fontManager.addfont(str(font_path))
        plt.rcParams['font.family'] = 'Microsoft YaHei'
    for input_path in args.inputs:
        render(input_path)


if __name__ == '__main__':
    main()
