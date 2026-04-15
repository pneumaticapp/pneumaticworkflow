// <reference types="jest" />
import { getVariableFromField } from '../getTaskVariables';
import { EExtraFieldType, IExtraField } from '../../../../../types/template';

describe('getVariableFromField', () => {
  const makeField = (overrides: Partial<IExtraField> = {}): IExtraField => ({
    apiName: 'field-1',
    name: 'Test Field',
    type: EExtraFieldType.Checkbox,
    order: 0,
    userId: null,
    groupId: null,
    ...overrides,
  });

  it('includes datasetId when field has dataset', () => {
    const field = makeField({ dataset: 5 });
    const result = getVariableFromField(field, 'Kick-off form');

    expect(result.datasetId).toBe(5);
  });

  it('does not include datasetId when field has no dataset', () => {
    const field = makeField();
    const result = getVariableFromField(field, 'Kick-off form');

    expect(result).not.toHaveProperty('datasetId');
  });

  it('normalizes object selections into string[]', () => {
    const field = makeField({
      selections: [
        { value: 'A', apiName: 'sel-1' },
        { value: 'B', apiName: 'sel-2' },
      ],
    });
    const result = getVariableFromField(field, 'Kick-off form');

    expect(result.selections).toEqual(['A', 'B']);
  });
});
