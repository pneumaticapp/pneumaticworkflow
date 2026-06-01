
import fieldsetsReducer, {
  initialState,
  loadFieldsets,
  setCurrentFieldset,
  updateFieldsetAction,
  removeFieldsetFromList,
  loadFieldsetsCatalogFailed,
  loadFieldsetsCatalogSuccess,
} from '../slice';
import { IFieldsetListItem } from '../../../types/fieldset';
import { makeFieldsetListItem, makeFieldsetTemplate } from '../../../__stubs__/fieldsets.factory';
import { IFieldsetsStore } from '../../../types/redux';

const makeStateWithList = (items: IFieldsetListItem[], overrides: Partial<IFieldsetsStore> = {}): IFieldsetsStore => ({
  ...initialState,
  fieldsetsList: { count: items.length, offset: 0, items },
  ...overrides,
});

describe('fieldsets slice', () => {
  describe('loadFieldsets', () => {
    it('clears the list when offset is 0 (template switch)', () => {
      const stateWithData: IFieldsetsStore = {
        ...initialState,
        fieldsetsList: {
          count: 2,
          offset: 0,
          items: [
            makeFieldsetListItem({ name: 'Fieldset from template A' }),
            makeFieldsetListItem({ id: 2, name: 'Another fieldset from template A' }),
          ],
        },
      };

      const result = fieldsetsReducer(stateWithData, loadFieldsets({ offset: 0, templateId: 999 }));

      expect(result.fieldsetsList.items).toEqual([]);
      expect(result.fieldsetsList.count).toBe(0);
      expect(result.fieldsetsList.offset).toBe(0);
      expect(result.isLoading).toBe(true);
    });

    it('keeps existing items when offset > 0 (pagination)', () => {
      const existingItems = [
        makeFieldsetListItem({ name: 'Fieldset 1' }),
        makeFieldsetListItem({ id: 2, name: 'Fieldset 2' }),
      ];
      const stateWithData: IFieldsetsStore = {
        ...initialState,
        fieldsetsList: {
          count: 5,
          offset: 0,
          items: existingItems,
        },
      };

      const result = fieldsetsReducer(stateWithData, loadFieldsets({ offset: 1, templateId: 123 }));

      expect(result.fieldsetsList.items).toHaveLength(2);
      expect(result.fieldsetsList.items).toEqual(existingItems);
      expect(result.isLoading).toBe(true);
    });
  });

  describe('setCurrentFieldset', () => {
    it('writes fieldset to currentFieldset and updates name/description in list', () => {
      const item = makeFieldsetListItem({ id: 5, name: 'Old Name' });
      const state = makeStateWithList([item]);
      const updated = makeFieldsetTemplate({ id: 5, name: 'New Name', description: 'New Desc' });

      const result = fieldsetsReducer(state, setCurrentFieldset(updated));

      expect(result.currentFieldset).toEqual(updated);
      expect(result.fieldsetsList.items[0].name).toBe('New Name');
      expect(result.fieldsetsList.items[0].description).toBe('New Desc');
    });

    it('does not crash or add phantom item when id is not in the list', () => {
      const state = makeStateWithList([makeFieldsetListItem({ name: 'Existing' })]);
      const fieldset = makeFieldsetTemplate({ id: 999 });

      const result = fieldsetsReducer(state, setCurrentFieldset(fieldset));

      expect(result.currentFieldset).toEqual(fieldset);
      expect(result.fieldsetsList.items).toHaveLength(1);
      expect(result.fieldsetsList.items[0].id).toBe(1);
    });
  });

  describe('updateFieldsetAction', () => {
    it('applies provided fields when id matches', () => {
      const state: IFieldsetsStore = {
        ...initialState,
        currentFieldset: makeFieldsetTemplate({ id: 5, name: 'Old', description: 'Desc' }),
      };

      const result = fieldsetsReducer(state, updateFieldsetAction({ id: 5, name: 'Updated' }));

      if (result.currentFieldset === null) throw new Error('expected currentFieldset');
      expect(result.currentFieldset.name).toBe('Updated');
      expect(result.currentFieldset.description).toBe('Desc');
    });

    it('does NOT apply when id does not match', () => {
      const state: IFieldsetsStore = {
        ...initialState,
        currentFieldset: makeFieldsetTemplate({ id: 5, name: 'Original' }),
      };

      const result = fieldsetsReducer(state, updateFieldsetAction({ id: 999, name: 'Should Not Apply' }));

      if (result.currentFieldset === null) throw new Error('expected currentFieldset');
      expect(result.currentFieldset.name).toBe('Original');
    });

    it('does NOT apply when currentFieldset is null', () => {
      const state: IFieldsetsStore = { ...initialState, currentFieldset: null };

      const result = fieldsetsReducer(state, updateFieldsetAction({ id: 5, name: 'Should Not Apply' }));

      expect(result.currentFieldset).toBeNull();
    });

    it('overwrites rules entirely', () => {
      const state: IFieldsetsStore = {
        ...initialState,
        currentFieldset: makeFieldsetTemplate({
          id: 5,
          rules: [{ id: 1, type: 'show', value: 'old', fields: [] }],
        }),
      };
      const newRules = [{ id: 2, type: 'hide', value: 'new', fields: ['f1'] }];

      const result = fieldsetsReducer(state, updateFieldsetAction({ id: 5, rules: newRules }));

      if (result.currentFieldset === null) throw new Error('expected currentFieldset');
      expect(result.currentFieldset.rules).toEqual(newRules);
    });
  });

  describe('removeFieldsetFromList', () => {
    it('removes item by id and decrements count', () => {
      const items = [makeFieldsetListItem({ name: 'A' }), makeFieldsetListItem({ id: 2, name: 'B' })];
      const state = makeStateWithList(items);

      const result = fieldsetsReducer(state, removeFieldsetFromList(1));

      expect(result.fieldsetsList.items).toHaveLength(1);
      expect(result.fieldsetsList.items[0].id).toBe(2);
      expect(result.fieldsetsList.count).toBe(1);
      expect(result.isLoading).toBe(false);
    });
  });

  describe('loadFieldsetsCatalogFailed', () => {
    it('resets isCatalogLoading and clears catalogLoadedForTemplateId', () => {
      const state: IFieldsetsStore = {
        ...initialState,
        isCatalogLoading: true,
        catalogLoadedForTemplateId: 42,
      };

      const result = fieldsetsReducer(state, loadFieldsetsCatalogFailed());

      expect(result.isCatalogLoading).toBe(false);
      expect(result.catalogLoadedForTemplateId).toBeNull();
    });
  });

  describe('loadFieldsetsCatalogSuccess', () => {
    it('writes catalogAllFieldsets and resets isCatalogLoading', () => {
      const state: IFieldsetsStore = { ...initialState, isCatalogLoading: true };
      const items = [makeFieldsetListItem({ name: 'A' }), makeFieldsetListItem({ id: 2, name: 'B' })];

      const result = fieldsetsReducer(state, loadFieldsetsCatalogSuccess(items));

      expect(result.catalogAllFieldsets).toEqual(items);
      expect(result.isCatalogLoading).toBe(false);
    });
  });
});
