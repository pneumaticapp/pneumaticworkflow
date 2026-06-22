
import { getFieldsetsCatalogByApiName } from '../fieldsets';
import { IApplicationState } from '../../../types/redux';
import { IFieldsetCatalogItem, EFieldsetsSorting } from '../../../types/fieldset';
import { makeFieldsetCatalogItem } from '../../../__stubs__/fieldsets.factory';

const makeState = (catalogItems: IFieldsetCatalogItem[]): IApplicationState => ({
  fieldsets: {
    templateId: null,
    fieldsetsList: { count: 0, offset: 0, items: [] },
    isLoading: false,
    searchQuery: '',
    fieldsetsListSorting: EFieldsetsSorting.DateDesc,
    isCreateModalOpen: false,
    isEditModalOpen: false,
    currentFieldset: null,
    isCurrentFieldsetLoading: false,
    catalogAllFieldsets: catalogItems,
    isCatalogLoading: false,
    catalogLoadedForTemplateId: null,
  },
} as unknown as IApplicationState);

describe('getFieldsetsCatalogByApiName', () => {
  it('returns the same Map object on repeated calls with the same state', () => {
    const items = [makeFieldsetCatalogItem({ id: 1, apiName: 'fs-1' })];
    const state = makeState(items);

    const result1 = getFieldsetsCatalogByApiName(state);
    const result2 = getFieldsetsCatalogByApiName(state);

    expect(result1).toBe(result2);
  });

  it('rebuilds the Map when items reference changes', () => {
    const items1 = [makeFieldsetCatalogItem({ id: 1, apiName: 'fs-1' })];
    const state1 = makeState(items1);
    const result1 = getFieldsetsCatalogByApiName(state1);

    const items2 = [makeFieldsetCatalogItem({ id: 2, apiName: 'fs-2' })];
    const state2 = makeState(items2);
    const result2 = getFieldsetsCatalogByApiName(state2);

    expect(result1).not.toBe(result2);
    expect(result2.has('fs-2')).toBe(true);
    expect(result2.has('fs-1')).toBe(false);
  });

  it('uses apiName as Map key', () => {
    const items = [makeFieldsetCatalogItem({ id: 42, apiName: 'my-custom-api-name' })];
    const state = makeState(items);

    const result = getFieldsetsCatalogByApiName(state);

    expect(result.has('my-custom-api-name')).toBe(true);
    expect(result.has('42')).toBe(false);
  });

  it('returns empty Map for empty catalogAllFieldsets', () => {
    const state = makeState([]);

    const result = getFieldsetsCatalogByApiName(state);

    expect(result.size).toBe(0);
  });

  it('keeps last item on apiName collision', () => {
    const items = [
      makeFieldsetCatalogItem({ id: 1, apiName: 'same-name', name: 'First' }),
      makeFieldsetCatalogItem({ id: 2, apiName: 'same-name', name: 'Second' }),
    ];
    const state = makeState(items);

    const result = getFieldsetsCatalogByApiName(state);

    expect(result.size).toBe(1);
    const entry = result.get('same-name');
    if (entry === undefined) throw new Error('expected entry for same-name');
    expect(entry.name).toBe('Second');
  });
});
