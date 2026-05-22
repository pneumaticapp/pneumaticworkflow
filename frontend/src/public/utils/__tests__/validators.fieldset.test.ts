// <reference types="jest" />

import { validateFieldsetName } from '../validators';

describe('validateFieldsetName', () => {
  it('returns error for empty name', () => {
    expect(validateFieldsetName('')).toBe('validation.fieldset-name-empty');
  });

  it('returns error for name longer than 200 characters', () => {
    const longName = 'a'.repeat(201);
    expect(validateFieldsetName(longName)).toBe('validation.fieldset-name-to-long');
  });

  it('passes for name exactly 200 characters', () => {
    expect(validateFieldsetName('a'.repeat(200))).toBe('');
  });
});
