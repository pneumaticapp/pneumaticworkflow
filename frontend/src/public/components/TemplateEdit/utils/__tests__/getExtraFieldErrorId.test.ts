import { getExtraFieldErrorId } from '../getExtraFieldErrorId';
import { makeExtraField } from '../../../../__stubs__/fields.factory';
import { EExtraFieldType, IExtraField } from '../../../../types/template';

describe('getExtraFieldErrorId', () => {
  const makeField = (overrides: Partial<IExtraField> = {}) =>
    makeExtraField({
      name: 'Test Field',
      type: EExtraFieldType.Checkbox,
      ...overrides,
    });

  it('accepts a Checkbox with a dataset and empty selections', () => {
    expect(getExtraFieldErrorId(makeField({ dataset: 5, selections: [] }))).toBe('');
  });

  it('reports an empty selection value of a Checkbox without a dataset', () => {
    const field = makeField({ selections: [{ apiName: 'sel-1', value: '', key: 1 }] });

    expect(getExtraFieldErrorId(field)).toBe('validation.kickoff-form-field-empty');
  });

  it('reports duplicate selection values', () => {
    const field = makeField({
      type: EExtraFieldType.Radio,
      selections: [
        { apiName: 'sel-1', value: 'Same', key: 1 },
        { apiName: 'sel-2', value: 'Same', key: 2 },
      ],
    });

    expect(getExtraFieldErrorId(field)).toBe('validation.checkbox-and-radio-value-duplicate');
  });

  it('reports an empty field name', () => {
    expect(getExtraFieldErrorId(makeField({ name: '', type: EExtraFieldType.String }))).toBe(
      'validation.kickoff-form-field-name-empty',
    );
  });

  it('accepts a Checkbox with filled selections', () => {
    const field = makeField({
      selections: [
        { apiName: 'sel-1', value: 'Option A', key: 1 },
        { apiName: 'sel-2', value: 'Option B', key: 2 },
      ],
    });

    expect(getExtraFieldErrorId(field)).toBe('');
  });
});
