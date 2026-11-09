import { getEmptySelection } from '../getEmptySelection';

describe('new selection labels', () => {
  it('preserves the original English default for existing callers', () => {
    expect(getEmptySelection().value).toBe('New option 1');
  });

  it('numbers new localized options without changing saved selections', () => {
    const existing = [
      { value: 'خيار جديد 2', apiName: 'arabic-option' },
      { value: 'New option 7', apiName: 'english-option' },
      { value: 'A custom answer', apiName: 'custom-option' },
    ];
    const before = JSON.stringify(existing);

    expect(getEmptySelection(existing, 'خيار جديد').value).toBe('خيار جديد 8');
    expect(JSON.stringify(existing)).toBe(before);
  });

  it('treats punctuation in a localized label as literal text', () => {
    const existing = [{ value: 'Option (new) 4', apiName: 'option' }];
    expect(getEmptySelection(existing, 'Option (new)').value).toBe('Option (new) 5');
  });
});
