import { normalizeSelections } from '../normalizeSelections';
import type { IExtraFieldSelection, IExtraFieldSelectionAPI } from '../../../../types/template';

describe('normalizeSelections', () => {
  it('returns empty array for undefined', () => {
    const result = normalizeSelections(undefined);
    expect(result).toEqual([]);
  });

  it('returns empty array for empty array', () => {
    const result = normalizeSelections([]);
    expect(result).toEqual([]);
  });

  it('returns string[] as-is when input is strings', () => {
    const input = ['a', 'b'];
    const result = normalizeSelections(input);
    expect(result).toEqual(['a', 'b']);
  });

  it('extracts .value from IExtraFieldSelection objects', () => {
    const input: IExtraFieldSelection[] = [
      { value: 'a', apiName: 'x' },
      { value: 'b', apiName: 'y' },
    ];
    const result = normalizeSelections(input);
    expect(result).toEqual(['a', 'b']);
  });

  describe('IExtraFieldSelectionAPI normalization', () => {
    it('extracts .value from objects with string apiName and dataset items with null apiName', () => {
      const input: IExtraFieldSelectionAPI[] = [
        { value: 'Yes', apiName: 'selection-1' },
        { value: 'From dataset', apiName: null },
      ];

      const result = normalizeSelections(input);

      expect(result).toEqual(['Yes', 'From dataset']);
    });

    it('extracts values from a mixed array of strings and selection objects', () => {
      const input: (IExtraFieldSelectionAPI | string)[] = ['Already string', { value: 'From object', apiName: null }];

      const result = normalizeSelections(input);

      expect(result).toEqual(['Already string', 'From object']);
    });
  });
});
