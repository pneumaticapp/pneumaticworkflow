import fieldsetsReducer, {
  initialState,
  loadFieldsets,
} from '../slice';
import { IFieldsetListItem } from '../../../types/fieldset';
import { IFieldsetsStore } from '../../../types/redux';

const createMockFieldsetItem = (id: number, name: string): IFieldsetListItem => ({
  id,
  apiName: `fieldset-${id}`,
  name,
  description: '',
  labelPosition: 'top',
  layout: 'vertical',
  order: id,
  kickoffId: null,
  taskId: null,
  rules: [],
  fields: [],
});

describe('fieldsets slice', () => {
  describe('loadFieldsets', () => {
    it('clears the fieldsets list when offset is 0 (template switch)', () => {
      const stateWithData: IFieldsetsStore = {
        ...initialState,
        fieldsetsList: {
          count: 2,
          offset: 0,
          items: [
            createMockFieldsetItem(1, 'Fieldset from template A'),
            createMockFieldsetItem(2, 'Another fieldset from template A'),
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
        createMockFieldsetItem(1, 'Fieldset 1'),
        createMockFieldsetItem(2, 'Fieldset 2'),
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
});
