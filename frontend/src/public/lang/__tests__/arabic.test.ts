import { parse, MessageFormatElement, TYPE } from '@formatjs/icu-messageformat-parser';
import { IntlMessageFormat } from 'intl-messageformat';
import { arMessages } from '../locales/ar-SY';
import { enMessages } from '../locales/en_US';

function argumentsOf(elements: MessageFormatElement[], names = new Set<string>()): string[] {
  elements.forEach((element) => {
    if (element.type !== TYPE.literal && element.type !== TYPE.pound) names.add(element.value);
    if (element.type === TYPE.select || element.type === TYPE.plural) {
      Object.values(element.options).forEach((option) => argumentsOf(option.value, names));
    }
    if (element.type === TYPE.tag) argumentsOf(element.children, names);
  });
  return Array.from(names).sort();
}

describe('Syrian Arabic catalogue', () => {
  it('covers every English key explicitly', () => {
    expect(Object.keys(arMessages).sort()).toEqual(Object.keys(enMessages).sort());
  });

  it.each(Object.keys(enMessages) as (keyof typeof enMessages)[])('%s preserves message arguments', (key) => {
    expect(argumentsOf(parse(arMessages[key]))).toEqual(argumentsOf(parse(enMessages[key])));
  });

  it.each([0, 1, 2, 3, 11, 102])('formats Arabic plural categories for %i', (count) => {
    expect(new IntlMessageFormat(arMessages['fieldsets.stats.fields'], 'ar-SY').format({ count })).toEqual(
      expect.any(String),
    );
  });
});
