import { getFromArray } from '../getFromArray';

describe('getFromArray', () => {
  it('returns the specified key from a single element of the array.', () => {
    const data = [{id: 1, name: 'Ivan'}, {id: 2, name: 'Peter'}];

    const result = getFromArray('name', data);

    expect(result).toEqual('Ivan');
  });

  it('returns the provided fallback if the element is not present in the array.', () => {
    const data: {id: number; name?: string}[] = [{ id: 1 }];

    const result = getFromArray('name', data, 'Unknown');

    expect(result).toEqual('Unknown');
  });
});
