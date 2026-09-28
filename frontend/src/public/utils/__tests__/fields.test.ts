import { normalizeCheckboxValue } from '../fields';
import { TExtraFieldValue } from '../../types/template';

describe('normalizeCheckboxValue', () => {
  it('should return the same array if an array of strings is passed', () => {
    const input = ['Option 1', 'Option 2'];
    expect(normalizeCheckboxValue(input)).toEqual(['Option 1', 'Option 2']);
  });

  it('should split a comma-separated string into an array of strings', () => {
    const input = 'Option 1, Option 2';
    expect(normalizeCheckboxValue(input)).toEqual(['Option 1', 'Option 2']);
  });

  it('should return a single item array for a string with one option', () => {
    const input = 'Option 1';
    expect(normalizeCheckboxValue(input)).toEqual(['Option 1']);
  });

  it('should return an empty array when an empty string is passed', () => {
    expect(normalizeCheckboxValue('')).toEqual([]);
    expect(normalizeCheckboxValue('   ')).toEqual([]);
  });

  it('should return an empty array for null or undefined', () => {
    expect(normalizeCheckboxValue(null)).toEqual([]);
    expect(normalizeCheckboxValue(undefined)).toEqual([]);
  });

  it('should return an empty array for non-string non-array values', () => {
    expect(normalizeCheckboxValue(123 as unknown as TExtraFieldValue)).toEqual([]);
    expect(normalizeCheckboxValue({} as unknown as TExtraFieldValue)).toEqual([]);
  });
});
