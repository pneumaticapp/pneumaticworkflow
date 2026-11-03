import { validateFieldsetName, validateFieldsetTitle } from '../validators';

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

describe('validateFieldsetTitle', () => {
  it('returns error for empty title', () => {
    expect(validateFieldsetTitle('')).toBe('validation.fieldset-title-empty');
  });

  it('returns error for title longer than 200 characters', () => {
    const longTitle = 'a'.repeat(201);
    expect(validateFieldsetTitle(longTitle)).toBe('validation.fieldset-title-to-long');
  });

  it('passes for title exactly 200 characters', () => {
    expect(validateFieldsetTitle('a'.repeat(200))).toBe('');
  });
});
