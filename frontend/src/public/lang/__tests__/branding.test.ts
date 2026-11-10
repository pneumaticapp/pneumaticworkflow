import { getBrandName, getOrganizationName } from '../../constants/branding';
import { enMessages } from '../locales/en_US';
import { ruMessages } from '../locales/ru_RU';
import { arMessages } from '../locales/ar-SY';

describe('display identity in locale catalogues', () => {
  it.each([
    ['en-US', enMessages],
    ['ru-RU', ruMessages],
    ['ar-SY', arMessages],
  ] as const)('uses canonical brand copy for %s and preserves actual provider contact details', (locale, messages) => {
    expect(messages['branding.product-name']).toBe(getBrandName(locale));
    expect(messages['branding.organization-name']).toBe(getOrganizationName(locale));
    expect(messages['general.pneumatic']).toBe(getBrandName(locale));
    expect(messages['public-form.pneumatic']).toBe(getBrandName(locale));
    expect(messages['integrations.support-email']).toBe('support@pneumatic.app');
    expect(messages['integrations.settings.zapier-description']).toContain('Zapier');
    for (const [id, message] of Object.entries(messages)) {
      if (id === 'integrations.support-email') continue;
      expect(message).not.toMatch(/\bPneumatic\b|Пневматик|пневматики/i);
    }
  });
});
