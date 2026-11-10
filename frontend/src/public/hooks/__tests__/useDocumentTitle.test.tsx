import React from 'react';
import { render } from '@testing-library/react';
import { IntlProvider } from 'react-intl';

import { useDocumentTitle } from '../useDocumentTitle';
import { PNEUMATIC_SUFFIX, TITLES, TDocumentTitle } from '../../constants/titles';
import { enMessages } from '../../lang/locales/en_US';
import { arMessages } from '../../lang/locales/ar-SY';
import { ruMessages } from '../../lang/locales/ru_RU';

jest.mock('react-intl', () => jest.requireActual('react-intl'));

function Probe({ title, content }: { title: TDocumentTitle; content?: string | null }) {
  useDocumentTitle(title, content);
  return null;
}

describe('localized document titles', () => {
  const originalTitle = document.title;
  const analyticsTitles = { ...TITLES };

  afterEach(() => {
    expect(TITLES).toEqual(analyticsTitles);
    document.title = originalTitle;
  });

  it.each(Object.keys(TITLES) as TDocumentTitle[])(
    'brands the English %s title while preserving the legacy analytics constant',
    (title) => {
      render(
        <IntlProvider locale="en-US" messages={enMessages}>
          <Probe title={title} />
        </IntlProvider>,
      );
      expect(document.title).toBe(TITLES[title].replace(PNEUMATIC_SUFFIX, '| Masarat'));
    },
  );

  it('updates a mounted page title when the active language changes', () => {
    const { rerender } = render(
      <IntlProvider locale="en-US" messages={enMessages}>
        <Probe title="Main" />
      </IntlProvider>,
    );
    expect(document.title).toBe('Dashboard | Masarat');

    rerender(
      <IntlProvider locale="ar-SY" messages={arMessages}>
        <Probe title="Main" />
      </IntlProvider>,
    );
    expect(document.title).toBe('لوحة المعلومات | مسارات');

    rerender(
      <IntlProvider locale="ru-RU" messages={ruMessages}>
        <Probe title="Main" />
      </IntlProvider>,
    );
    expect(document.title).toBe('Панель управления | Masarat');
  });

  it('preserves user-entered workflow/task names and falls back to the localized page title while loading', () => {
    const content = 'معاملة إسكان — Pneumatic legacy 42';
    const { rerender } = render(
      <IntlProvider locale="ar-SY" messages={arMessages}>
        <Probe title="TasksDetail" content={content} />
      </IntlProvider>,
    );
    expect(document.title).toBe(`${content} | مسارات`);

    rerender(
      <IntlProvider locale="en-US" messages={enMessages}>
        <Probe title="TasksDetail" content={content} />
      </IntlProvider>,
    );
    expect(document.title).toBe(`${content} | Masarat`);

    rerender(
      <IntlProvider locale="ar-SY" messages={arMessages}>
        <Probe title="TasksDetail" />
      </IntlProvider>,
    );
    expect(document.title).toBe('المهمة | مسارات');
  });
});
