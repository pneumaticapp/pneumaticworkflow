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
});
