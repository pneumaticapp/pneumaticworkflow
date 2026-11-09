import React from 'react';
import { render, screen } from '@testing-library/react';

import { ErrorFallback } from '../ErrorFallback';
import { AppLocale } from '../../../lang';
import { resolveLocale } from '../../../lang/locale';

jest.mock('react-intl', () => jest.requireActual('react-intl'));
jest.mock('../../../utils/sentryCapture', () => ({ captureException: jest.fn() }));

describe('error fallback outside IntlProvider', () => {
  const originalLanguage = document.documentElement.lang;

  afterEach(() => {
    document.documentElement.lang = originalLanguage;
  });

  it.each(['en-US', 'ar-SY', 'unknown'])('uses a safe catalogue lookup for document language %s', (language) => {
    document.documentElement.lang = language;
    render(<ErrorFallback error={new Error('Technical error details')} />);

    expect(screen.getByText(AppLocale[resolveLocale(language)].messages['pages.error-fallback'])).toBeVisible();
    expect(screen.getByText('Technical error details')).toBeVisible();
  });
});
