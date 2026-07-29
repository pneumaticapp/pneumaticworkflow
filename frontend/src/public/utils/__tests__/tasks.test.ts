import { getNormalizedTask } from '../tasks';
import { EFieldLabelPosition } from '../../types/fieldset';
import { makeExtraField } from '../../__stubs__/fields.factory';
import { makeFieldsetTaskAPI } from '../../__stubs__/fieldsets.factory';
import { makeTaskAPI } from '../../__stubs__/tasks.factory';

describe('getNormalizedTask', () => {
  describe('fieldset normalization', () => {
    it('maps IFieldsetTaskAPI[] to IFieldsetRuntime[] via mapFieldsetTaskAPIToRuntime', () => {
      const task = makeTaskAPI({
        fieldsets: [
          makeFieldsetTaskAPI({ id: 50, apiName: 'fs-binding-abc', name: 'Budget' }),
        ],
      });

      const result = getNormalizedTask(task);

      expect(result.fieldsets).toHaveLength(1);
      expect(result.fieldsets[0].apiNameBinding).toBe('fs-binding-abc');
      expect(result.fieldsets[0].name).toBe('Budget');
      expect(result.fieldsets[0]).not.toHaveProperty('id');
      expect(result.fieldsets[0]).not.toHaveProperty('apiName');
    });

    it('maps multiple fieldsets preserving order and properties', () => {
      const task = makeTaskAPI({
        fieldsets: [
          makeFieldsetTaskAPI({ id: 1, apiName: 'fs-a', name: 'A', order: 0 }),
          makeFieldsetTaskAPI({
            id: 2,
            apiName: 'fs-b',
            name: 'B',
            order: 5,
            labelPosition: EFieldLabelPosition.Left,
            layout: 'horizontal',
            fields: [makeExtraField({ apiName: 'ef-1', name: 'Amount' })],
          }),
        ],
      });

      const result = getNormalizedTask(task);

      expect(result.fieldsets).toHaveLength(2);
      expect(result.fieldsets[0].apiNameBinding).toBe('fs-a');
      expect(result.fieldsets[1].apiNameBinding).toBe('fs-b');
      expect(result.fieldsets[1].labelPosition).toBe(EFieldLabelPosition.Left);
      expect(result.fieldsets[1].layout).toBe('horizontal');
      expect(result.fieldsets[1].fields).toHaveLength(1);
    });

    it('returns empty fieldsets array when task has no fieldsets', () => {
      const task = makeTaskAPI({ fieldsets: [] });

      const result = getNormalizedTask(task);

      expect(result.fieldsets).toEqual([]);
    });
  });
});
