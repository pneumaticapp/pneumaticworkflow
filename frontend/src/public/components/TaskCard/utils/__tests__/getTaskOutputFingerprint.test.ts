import { EExtraFieldType } from '../../../../types/template';
import { getTaskOutputFingerprint } from '../getTaskOutputFingerprint';

describe('getTaskOutputFingerprint', () => {
  it('returns the same fingerprint when output array reference changes but data is equal', () => {
    const fields = [
      {
        apiName: 'url-field',
        name: 'URL',
        type: EExtraFieldType.Url,
        order: 1,
        value: 'https://example.com',
        userId: null,
        groupId: null,
      },
    ];

    expect(getTaskOutputFingerprint(fields)).toBe(getTaskOutputFingerprint([...fields]));
  });

  it('returns a different fingerprint when server field values change', () => {
    const base = {
      apiName: 'url-field',
      name: 'URL',
      type: EExtraFieldType.Url,
      order: 1,
      userId: null,
      groupId: null,
    };

    expect(
      getTaskOutputFingerprint([{ ...base, value: 'https://a.example' }]),
    ).not.toBe(
      getTaskOutputFingerprint([{ ...base, value: 'https://b.example' }]),
    );
  });

  it.each([
    ['name', 'Updated URL'],
    ['description', 'Updated description'],
    ['isRequired', true],
    ['isHidden', true],
    ['selections', ['first', 'second']],
    ['dataset', 42],
  ])('returns a different fingerprint when %s changes', (property, value) => {
    const field = {
      apiName: 'url-field',
      name: 'URL',
      description: '',
      type: EExtraFieldType.Url,
      order: 1,
      value: 'https://example.com',
      userId: null,
      groupId: null,
    };

    expect(getTaskOutputFingerprint([field])).not.toBe(
      getTaskOutputFingerprint([{ ...field, [property]: value }]),
    );
  });
});
