// <reference types="jest" />
import { validateDatasetName, validateDatasetRow } from '../validators';

describe('validateDatasetName', () => {
  it('returns error for empty name', () => {
    expect(validateDatasetName('')).toBe('validation.dataset-name-empty');
  });

  it('returns error for name longer than 200 characters', () => {
    const longName = 'x'.repeat(201);
    expect(validateDatasetName(longName)).toBe('validation.dataset-name-to-long');
  });

  it('returns empty string for valid name', () => {
    expect(validateDatasetName('My Dataset')).toBe('');
  });
});

describe('validateDatasetRow', () => {
  it('returns error for empty value', () => {
    expect(validateDatasetRow('', ['Banana'])).toBe('validation.dataset-row-empty');
  });

  it('returns error for case-insensitive duplicate', () => {
    expect(validateDatasetRow('Apple', ['apple', 'Banana'])).toBe('validation.dataset-row-exists');
  });

  it('excludes own value when editing (excludeValue)', () => {
    expect(validateDatasetRow('Apple', ['Apple', 'Banana'], 'Apple')).toBe('');
  });

  it('returns empty string for valid unique value', () => {
    expect(validateDatasetRow('Cherry', ['Apple', 'Banana'])).toBe('');
  });
});
