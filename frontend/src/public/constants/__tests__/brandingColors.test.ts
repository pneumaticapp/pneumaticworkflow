import fs from 'fs';
import path from 'path';

import { EBrandColors } from '../brandColors';
import { EProgressbarColor } from '../../components/Workflows/utils/getWorfkflowClientProperties';

const palette = {
  forest: EBrandColors.Forest,
  'forest-dark': EBrandColors.ForestDark,
  'forest-deep': EBrandColors.ForestDeep,
  'wheat-light': EBrandColors.WheatLight,
  wheat: EBrandColors.Wheat,
  'wheat-dark': EBrandColors.WheatDark,
  umber: EBrandColors.Umber,
  'umber-dark': EBrandColors.UmberDark,
  'umber-deep': EBrandColors.UmberDeep,
  white: EBrandColors.White,
  charcoal: EBrandColors.Charcoal,
  'charcoal-dark': EBrandColors.CharcoalDark,
};

function luminance(hex: string): number {
  const rgb = hex
    .slice(1)
    .match(/../g)!
    .map((channel) => {
      const value = parseInt(channel, 16) / 255;
      return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
    });
  return rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722;
}

function contrast(first: string, second: string): number {
  const values = [luminance(first), luminance(second)].sort((a, b) => b - a);
  return (values[0] + 0.05) / (values[1] + 0.05);
}

describe('approved Ministry palette across the existing styling systems', () => {
  const css = fs.readFileSync(path.resolve(__dirname, '../../assets/css/variables/color.css'), 'utf8');
  const sass = fs.readFileSync(path.resolve(__dirname, '../../assets/css/sass/_branding.scss'), 'utf8');

  it.each(Object.entries(palette))('keeps %s identical for CSS, Sass and SVG/canvas', (name, value) => {
    expect(css).toContain(`--brand-${name}: ${value};`);
    expect(sass).toContain(`$brand-${name}: ${value};`);
  });

  it.each([
    ['primary action', EBrandColors.ForestDark, EBrandColors.White],
    ['hover action', EBrandColors.ForestDeep, EBrandColors.White],
    ['secondary action', EBrandColors.Forest, EBrandColors.White],
    ['gold accent', EBrandColors.Wheat, EBrandColors.CharcoalDark],
    ['sidebar active item', EBrandColors.ForestDeep, EBrandColors.Wheat],
    ['warm surface', EBrandColors.WheatLight, EBrandColors.Charcoal],
    ['destructive action', EBrandColors.Umber, EBrandColors.White],
  ])('preserves AA normal-text contrast for %s', (_, background, foreground) => {
    expect(contrast(background, foreground)).toBeGreaterThanOrEqual(4.5);
  });

  it.each([EBrandColors.White, EBrandColors.WheatLight])(
    'keeps meaningful active/completed/overdue progress marks visible on %s',
    (surface) => {
      [EProgressbarColor.Yellow, EProgressbarColor.Green, EProgressbarColor.Red].forEach((color) => {
        expect(contrast(color, surface)).toBeGreaterThanOrEqual(3);
      });
    },
  );
});
