import React from 'react';
import { render, screen } from '@testing-library/react';
import { IntlProvider } from 'react-intl';

import { Copyright } from '../Copyright';
import { BRAND, getBrandName } from '../../../../../constants/branding';
import { enMessages } from '../../../../../lang/locales/en_US';
import { arMessages } from '../../../../../lang/locales/ar-SY';

jest.mock('react-intl', () => jest.requireActual('react-intl'));

describe('public form brand attribution', () => {
  it.each([
    ['en-US', enMessages],
    ['ar-SY', arMessages],
  ] as const)('links the %s display brand to the application home', (locale, messages) => {
    render(
      <IntlProvider locale={locale} messages={messages}>
        <Copyright />
      </IntlProvider>,
    );

    expect(screen.getByRole('link', { name: getBrandName(locale) })).toHaveAttribute('href', BRAND.homePath);
  });
});
