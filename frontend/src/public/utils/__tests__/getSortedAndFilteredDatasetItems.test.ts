// <reference types="jest" />
import { getSortedAndFilteredDatasetItems } from '../dataset';
import { EDatasetsSorting, IDatasetItem } from '../../types/dataset';

describe('getSortedAndFilteredDatasetItems', () => {
  const makeItem = (value: string, order: number): IDatasetItem => ({ value, order });

  const items: IDatasetItem[] = [
    makeItem('Banana', 2),
    makeItem('Apple', 4),
    makeItem('Cherry', 1),
    makeItem('Apricot', 3),
  ];

  it('filters by searchText (case-insensitive)', () => {
    const result = getSortedAndFilteredDatasetItems(items, 'app', EDatasetsSorting.DateDesc);
    expect(result).toHaveLength(1);
    expect(result[0].value).toBe('Apple');
  });

  it('returns all items when searchText is empty', () => {
    const result = getSortedAndFilteredDatasetItems(items, '', EDatasetsSorting.DateDesc);
    expect(result).toHaveLength(4);
  });

  it('sorts by name ascending (NameAsc)', () => {
    const result = getSortedAndFilteredDatasetItems(items, '', EDatasetsSorting.NameAsc);
    const values = result.map((i) => i.value);
    expect(values).toEqual(['Apple', 'Apricot', 'Banana', 'Cherry']);
  });

  it('sorts by name descending (NameDesc)', () => {
    const result = getSortedAndFilteredDatasetItems(items, '', EDatasetsSorting.NameDesc);
    const values = result.map((i) => i.value);
    expect(values).toEqual(['Cherry', 'Banana', 'Apricot', 'Apple']);
  });

  it('sorts by order ascending (DateAsc)', () => {
    const result = getSortedAndFilteredDatasetItems(items, '', EDatasetsSorting.DateAsc);
    const values = result.map((i) => i.value);
    expect(values).toEqual(['Cherry', 'Banana', 'Apricot', 'Apple']);
  });

  it('sorts by order descending (DateDesc, default)', () => {
    const result = getSortedAndFilteredDatasetItems(items, '', EDatasetsSorting.DateDesc);
    const values = result.map((i) => i.value);
    expect(values).toEqual(['Apple', 'Apricot', 'Banana', 'Cherry']);
  });

  it('filters first, then sorts (searchText + NameAsc)', () => {
    const result = getSortedAndFilteredDatasetItems(items, 'a', EDatasetsSorting.NameAsc);
    const values = result.map((i) => i.value);
    expect(values).toEqual(['Apple', 'Apricot', 'Banana']);
  });
});
