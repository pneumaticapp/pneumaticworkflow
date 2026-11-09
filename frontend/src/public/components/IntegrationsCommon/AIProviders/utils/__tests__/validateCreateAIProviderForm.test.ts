import { EAIVendor } from '../../../../../api/ai/types';
import type { IAIProvider } from '../../../../../api/ai/types';
import { ECreateAIProviderTab } from '../../types';
import { validateCreateAIProviderForm } from '../validateCreateAIProviderForm';

const providers: IAIProvider[] = [
  {
    id: 1,
    name: 'OpenRouter',
    baseUrl: 'https://openrouter.ai/api/v1',
    apiKeyPrefix: 'sk-',
    vendor: EAIVendor.OpenRouter,
    usage: [],
  },
];
const vendors = [
  { slug: 'openrouter', name: 'OpenRouter' },
  { slug: 'openai', name: 'OpenAI' },
];
const emptyValues = { vendor: '', name: '', baseUrl: '', apiKey: '' };

describe('validateCreateAIProviderForm', () => {
  it('requires only the vendor tab fields on the vendor tab', () => {
    expect(Object.keys(validateCreateAIProviderForm(emptyValues, ECreateAIProviderTab.Vendor, [], vendors))).toEqual([
      'vendor',
      'apiKey',
    ]);
  });

  it('requires only the custom tab fields on the custom tab', () => {
    expect(Object.keys(validateCreateAIProviderForm(emptyValues, ECreateAIProviderTab.Custom, [], vendors))).toEqual([
      'name',
      'baseUrl',
      'apiKey',
    ]);
  });

  it('rejects a vendor whose provider already exists', () => {
    const errors = validateCreateAIProviderForm(
      { ...emptyValues, vendor: 'openrouter', apiKey: 'key' },
      ECreateAIProviderTab.Vendor,
      providers,
      vendors,
    );

    expect(errors).toEqual({ vendor: 'ai-providers.name-exists' });
  });

  it('rejects a custom name that matches an existing provider ignoring case and spaces', () => {
    const errors = validateCreateAIProviderForm(
      { ...emptyValues, name: '  openrouter ', baseUrl: 'https://x', apiKey: 'key' },
      ECreateAIProviderTab.Custom,
      providers,
      vendors,
    );

    expect(errors).toEqual({ name: 'ai-providers.name-exists' });
  });

  it('accepts a new vendor and a unique custom name', () => {
    expect(
      validateCreateAIProviderForm(
        { ...emptyValues, vendor: 'openai', apiKey: 'key' },
        ECreateAIProviderTab.Vendor,
        providers,
        vendors,
      ),
    ).toEqual({});
    expect(
      validateCreateAIProviderForm(
        { ...emptyValues, name: 'Mine', baseUrl: 'https://x', apiKey: 'key' },
        ECreateAIProviderTab.Custom,
        providers,
        vendors,
      ),
    ).toEqual({});
  });
});
