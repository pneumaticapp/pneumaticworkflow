import { EExtraFieldType } from '../../types/template';
import { makeExtraField } from '../../__stubs__/fields.factory';
import { mapTspToString } from '../mappers';

describe('mapTspToString', () => {
  it('formats numeric unix date fields', () => {
    const output = [
      makeExtraField({
        type: EExtraFieldType.Date,
        value: 1718409600,
      }),
    ];

    expect(mapTspToString(output, 'UTC')[0].value).toMatch(/15, 2024/);
  });

  it('formats string unix date fields', () => {
    const output = [
      makeExtraField({
        type: EExtraFieldType.Date,
        value: '1718409600',
      }),
    ];

    expect(mapTspToString(output, 'UTC')[0].value).toMatch(/15, 2024/);
  });

  it('leaves non-date fields unchanged', () => {
    const output = [
      makeExtraField({
        type: EExtraFieldType.String,
        value: 'keep-me',
      }),
    ];

    expect(mapTspToString(output, 'UTC')[0].value).toBe('keep-me');
  });
});
