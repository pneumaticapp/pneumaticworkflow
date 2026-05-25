import {
  validateRegistrationPassword,
  REGISTRATION_PASSWORD_MSG_EMPTY,
  REGISTRATION_PASSWORD_MSG_SPACES,
  REGISTRATION_PASSWORD_MSG_TOO_SHORT,
} from '../validators';

describe('validateRegistrationPassword', () => {
  it('returns empty message when value is empty', () => {
    expect(validateRegistrationPassword('')).toBe(REGISTRATION_PASSWORD_MSG_EMPTY);
  });

  it('returns spaces message when value contains spaces', () => {
    expect(validateRegistrationPassword('123 456')).toBe(REGISTRATION_PASSWORD_MSG_SPACES);
  });

  it('returns too-short message when length < 6', () => {
    expect(validateRegistrationPassword('12345')).toBe(REGISTRATION_PASSWORD_MSG_TOO_SHORT);
  });

  it('returns empty string when valid (6+ chars, no spaces)', () => {
    expect(validateRegistrationPassword('123456')).toBe('');
  });
});
