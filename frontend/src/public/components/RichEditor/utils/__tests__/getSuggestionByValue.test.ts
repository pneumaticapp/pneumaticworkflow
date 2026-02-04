import { getSuggestionByValue } from '../getSuggestionByValue';

describe('getSuggestionByValue', () => {
  const suggestions = [
    { id: 1, name: 'Alice' },
    { id: 2, name: 'Bob' },
    { id: 3, name: 'Charlie' },
    { id: 4, name: 'Anna' },
  ];

  it('returns all suggestions when value is empty', () => {
    expect(getSuggestionByValue('', suggestions)).toEqual(suggestions);
  });

  it('filters suggestions by name (case-insensitive)', () => {
    expect(getSuggestionByValue('al', suggestions)).toEqual([{ id: 1, name: 'Alice' }]);
    expect(getSuggestionByValue('AN', suggestions)).toEqual([{ id: 4, name: 'Anna' }]);
    expect(getSuggestionByValue('ob', suggestions)).toEqual([{ id: 2, name: 'Bob' }]);
  });

  it('returns single match for full name', () => {
    expect(getSuggestionByValue('Bob', suggestions)).toEqual([{ id: 2, name: 'Bob' }]);
  });

  it('returns empty array when no match', () => {
    expect(getSuggestionByValue('xyz', suggestions)).toEqual([]);
  });

  it('returns empty array when suggestions is empty', () => {
    expect(getSuggestionByValue('al', [])).toEqual([]);
  });
});
