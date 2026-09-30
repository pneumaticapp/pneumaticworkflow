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

  it('normalizes equivalent empty values', () => {
    const field = {
      apiName: 'field',
      name: 'Field',
      type: EExtraFieldType.String,
      order: 1,
      userId: null,
      groupId: null,
    };
    const emptyValues = [undefined, null, '', []];
    const fingerprints = emptyValues.map((value) => getTaskOutputFingerprint([{ ...field, value }]));

    expect(new Set(fingerprints).size).toBe(1);
  });

  it('normalizes equivalent empty file representations', () => {
    const fileField = {
      apiName: 'file-field',
      name: 'File',
      type: EExtraFieldType.File,
      order: 1,
      value: [],
      userId: null,
      groupId: null,
    };

    expect(getTaskOutputFingerprint([fileField])).toBe(
      getTaskOutputFingerprint([
        {
          ...fileField,
          attachments: [],
          markdownValue: '',
        },
      ]),
    );
  });

  it('normalizes undefined and false attachment isRemoved flags', () => {
    const baseAttachment = {
      id: 'file-id',
      name: 'file.pdf',
      url: 'https://files.example/file.pdf',
      size: 100,
    };
    const fileField = {
      apiName: 'file-field',
      name: 'File',
      type: EExtraFieldType.File,
      order: 1,
      value: [],
      userId: null,
      groupId: null,
      markdownValue: '[file.pdf](https://files.example/file.pdf)',
    };

    expect(
      getTaskOutputFingerprint([
        {
          ...fileField,
          attachments: [{ ...baseAttachment }],
        },
      ]),
    ).toBe(
      getTaskOutputFingerprint([
        {
          ...fileField,
          attachments: [{ ...baseAttachment, isRemoved: false }],
        },
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

    expect(getTaskOutputFingerprint([{ ...base, value: 'https://a.example' }])).not.toBe(
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

    expect(getTaskOutputFingerprint([field])).toBe(getTaskOutputFingerprint([{ ...field, [property]: metadataValue }]));
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

  it('returns the same fingerprint for a file field when files arrive as markdown or as attachments', () => {
    const fileField = {
      apiName: 'file-field',
      name: 'File',
      type: EExtraFieldType.File,
      order: 1,
      value: [],
      userId: null,
      groupId: null,
    };
    const attachment = { id: 'file-id', name: 'file.pdf', url: 'https://files.example/file.pdf', size: 100 };

    expect(
      getTaskOutputFingerprint([{ ...fileField, markdownValue: '[file.pdf](https://files.example/file.pdf)' }]),
    ).toBe(getTaskOutputFingerprint([{ ...fileField, attachments: [attachment] }]));
  });

  it('returns the same fingerprint for a file field when attachments arrive in a different order', () => {
    const fileField = {
      apiName: 'file-field',
      name: 'File',
      type: EExtraFieldType.File,
      order: 1,
      value: [],
      userId: null,
      groupId: null,
    };
    const firstFile = { id: 'a', name: 'a.pdf', url: 'https://files.example/a.pdf', size: 1 };
    const secondFile = { id: 'b', name: 'b.pdf', url: 'https://files.example/b.pdf', size: 1 };

    expect(getTaskOutputFingerprint([{ ...fileField, attachments: [firstFile, secondFile] }])).toBe(
      getTaskOutputFingerprint([{ ...fileField, attachments: [secondFile, firstFile] }]),
    );
  });

  it('returns the same fingerprint for a file field when only the derived value array differs', () => {
    const fileField = {
      apiName: 'file-field',
      name: 'File',
      type: EExtraFieldType.File,
      order: 1,
      userId: null,
      groupId: null,
      markdownValue: '[file.pdf](https://files.example/file.pdf)',
    };
    const attachment = { id: 'file-id', name: 'file.pdf', url: 'https://files.example/file.pdf', size: 100 };

    expect(getTaskOutputFingerprint([{ ...fileField, value: [] }])).toBe(
      getTaskOutputFingerprint([
        { ...fileField, attachments: [attachment], value: ['[file.pdf](https://files.example/file.pdf)'] },
      ]),
    );
  });

  it('returns a different fingerprint for a file field when the file set changes', () => {
    const fileField = {
      apiName: 'file-field',
      name: 'File',
      type: EExtraFieldType.File,
      order: 1,
      value: [],
      userId: null,
      groupId: null,
    };
    const attachment = { id: 'file-id', name: 'file.pdf', url: 'https://files.example/file.pdf', size: 100 };

    expect(getTaskOutputFingerprint([{ ...fileField, attachments: [attachment] }])).not.toBe(
      getTaskOutputFingerprint([
        {
          ...fileField,
          attachments: [
            attachment,
            { id: 'other', name: 'other.pdf', url: 'https://files.example/other.pdf', size: 1 },
          ],
        },
      ]),
    );
  });
});
