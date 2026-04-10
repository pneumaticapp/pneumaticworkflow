// <reference types="jest" />
import { areExtraFieldsValid } from '../areExtraFieldsValid';
import { EExtraFieldType, IExtraField } from '../../../../types/template';

describe('areExtraFieldsValid', () => {
  const makeField = (overrides: Partial<IExtraField> = {}): IExtraField => ({
    apiName: 'field-1',
    name: 'Test Field',
    type: EExtraFieldType.Checkbox,
    order: 0,
    userId: null,
    groupId: null,
    ...overrides,
  });

  it('returns valid when Checkbox has dataset and empty selections (dataset bypass)', () => {
    const fields = [makeField({ dataset: 5, selections: [] })];
    expect(areExtraFieldsValid(fields)).toBe(true);
  });

  it('returns invalid when Checkbox has no dataset and empty selection value', () => {
    const fields = [
      makeField({
        selections: [{ apiName: 'sel-1', value: '', key: 1 }],
      }),
    ];
    expect(areExtraFieldsValid(fields)).toBe(false);
  });

  it('returns valid when Checkbox has no dataset and filled selections', () => {
    const fields = [
      makeField({
        selections: [
          { apiName: 'sel-1', value: 'Option A', key: 1 },
          { apiName: 'sel-2', value: 'Option B', key: 2 },
        ],
      }),
    ];
    expect(areExtraFieldsValid(fields)).toBe(true);
  });
});
