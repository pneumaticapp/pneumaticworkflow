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

  it('returns the same fingerprint when metadata ordering changes', () => {
    const firstField = {
      apiName: 'first-field',
      name: 'First',
      type: EExtraFieldType.Url,
      order: 1,
      value: 'https://first.example.com',
      userId: null,
      groupId: null,
    };
    const secondField = {
      ...firstField,
      apiName: 'second-field',
      name: 'Second',
      order: 0,
      value: 'https://second.example.com',
    };

    expect(getTaskOutputFingerprint([firstField, secondField])).toBe(
      getTaskOutputFingerprint([
        { ...secondField, order: 2 },
        { ...firstField, order: 0 },
      ]),
    );
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
    ['order', 2],
  ])('returns the same fingerprint when %s metadata changes', (property, metadataValue) => {
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

    expect(getTaskOutputFingerprint([field])).toBe(
      getTaskOutputFingerprint([{ ...field, [property]: metadataValue }]),
    );
  });

  it.each([
    ['value', 'https://updated.example'],
    ['userId', 42],
    ['groupId', 24],
    ['markdownValue', '[file.pdf](https://files.example/file.pdf)'],
    ['attachments', [{ id: 'file-id', name: 'file.pdf', url: 'https://files.example/file.pdf', size: 100 }]],
  ])('returns a different fingerprint when submitted %s changes', (property, submittedValue) => {
    const field = {
      apiName: 'url-field',
      name: 'URL',
      type: EExtraFieldType.Url,
      order: 1,
      value: 'https://example.com',
      userId: null,
      groupId: null,
    };

    expect(getTaskOutputFingerprint([field])).not.toBe(
      getTaskOutputFingerprint([{ ...field, [property]: submittedValue }]),
    );
  });
});
