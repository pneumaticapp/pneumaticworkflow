import { EDatasetsSorting, IDatasetItem } from '../types/dataset';

export function getSortedAndFilteredDatasetItems(
  items: IDatasetItem[],
  searchText: string,
  sorting: EDatasetsSorting,
): IDatasetItem[] {
  let result = [...items];

  if (searchText) {
    const lowerSearch = searchText.toLowerCase();
    result = result.filter(item => item.value.toLowerCase().includes(lowerSearch));
  }

  result.sort((a, b) => {
    if (sorting === EDatasetsSorting.NameAsc) {
      return a.value.localeCompare(b.value, undefined, { numeric: true });
    }
    if (sorting === EDatasetsSorting.NameDesc) {
      return b.value.localeCompare(a.value, undefined, { numeric: true });
    }
    if (sorting === EDatasetsSorting.DateAsc) {
      return a.order - b.order;
    }

    return b.order - a.order;
  });

  return result;
}
