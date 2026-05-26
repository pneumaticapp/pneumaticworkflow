// <reference types="jest" />
import { normalizeSelections } from '../normalizeSelections';
import { IExtraFieldSelection } from '../../../../types/template';

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
});
