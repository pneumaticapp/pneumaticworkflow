// <reference types="jest" />
import { shouldLoadDatasetForVariable } from '../shouldLoadDatasetForVariable';
import { EExtraFieldType } from '../../../../../../types/template';
import { TTaskVariable } from '../../../../types';

describe('shouldLoadDatasetForVariable', () => {
  const makeVariable = (overrides: Partial<TTaskVariable> = {}): TTaskVariable => ({
    apiName: 'field-1',
    title: 'Test',
    type: EExtraFieldType.String,
    ...overrides,
  });

  it('returns true for Checkbox with datasetId', () => {
    const variable = makeVariable({ type: EExtraFieldType.Checkbox, datasetId: 5 });
    expect(shouldLoadDatasetForVariable(variable)).toBe(true);
  });

  it('returns true for Radio with datasetId', () => {
    const variable = makeVariable({ type: EExtraFieldType.Radio, datasetId: 3 });
    expect(shouldLoadDatasetForVariable(variable)).toBe(true);
  });

  it('returns true for Creatable with datasetId', () => {
    const variable = makeVariable({ type: EExtraFieldType.Creatable, datasetId: 1 });
    expect(shouldLoadDatasetForVariable(variable)).toBe(true);
  });

  it('returns false for Checkbox without datasetId', () => {
    const variable = makeVariable({ type: EExtraFieldType.Checkbox, datasetId: undefined });
    expect(shouldLoadDatasetForVariable(variable)).toBe(false);
  });

  it('returns false for non-list field type with datasetId', () => {
    const variable = makeVariable({ type: EExtraFieldType.String, datasetId: 5 });
    expect(shouldLoadDatasetForVariable(variable)).toBe(false);
  });

  it('returns false for non-list field type without datasetId', () => {
    const variable = makeVariable({ type: EExtraFieldType.String, datasetId: undefined });
    expect(shouldLoadDatasetForVariable(variable)).toBe(false);
  });
});
