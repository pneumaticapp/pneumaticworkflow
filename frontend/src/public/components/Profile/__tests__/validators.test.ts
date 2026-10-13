import { validateProfilePhone } from '../validators';

describe('validateProfilePhone', () => {
  it('requires a phone number and validates its format', () => {
    expect(validateProfilePhone('')).toBe('validation.phone-number-empty');
    expect(validateProfilePhone('123')).toBe('validation.phone-number-invalid');
    expect(validateProfilePhone('+14155552671')).toBe('');
  });
});
