import { getPlainText } from '../getPlainText';

describe('getPlainText', () => {
  it('should strip HTML tags and collapse whitespace', () => {
    expect(getPlainText('<p>Hello&nbsp;<strong>world</strong></p>')).toBe('Hello world');
  });

  it('should return an empty string for markup without text', () => {
    expect(getPlainText('<p><br></p>')).toBe('');
  });

  it('should return an empty string when value is missing', () => {
    expect(getPlainText(undefined)).toBe('');
    expect(getPlainText(null)).toBe('');
  });
});
