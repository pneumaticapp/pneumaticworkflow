import { ContentState } from 'draft-js';
import { convertDraftToText } from '../convertDraftToText';

describe('convertDraftToText', () => {
  it('converts plain text to string', () => {
    const contentState = ContentState.createFromText('Hello world');
    expect(convertDraftToText(contentState)).toBe('Hello world');
  });

  it('converts empty content to empty string', () => {
    const contentState = ContentState.createFromText('');
    expect(convertDraftToText(contentState)).toBe('');
  });

  it('converts multiline content preserving newlines', () => {
    const contentState = ContentState.createFromText('Line one\nLine two');
    expect(convertDraftToText(contentState)).toContain('Line one');
    expect(convertDraftToText(contentState)).toContain('Line two');
  });
});
