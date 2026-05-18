// <reference types="jest" />
import { IExtraField, IFieldsetData, ITaskFieldset } from '../../../../types/template';
import {
  buildMergedTaskOutputRows,
  buildRuntimeMergedOutputParts,
  buildRowsWithAddedFieldset,
  buildRowsWithRemovedFieldset,
  moveMergedRow,
  normalizeMergedTaskOutputOrders,
} from '../mergeTaskOutputFlow';

const field = (apiName: string, order: number): IExtraField => ({
  apiName,
  name: apiName,
  type: 'string' as IExtraField['type'],
  order,
  isRequired: false,
  isHidden: false,
  userId: null,
  groupId: null,
});

const fs = (id: number, order: number): IFieldsetData => ({
  id,
  apiName: `fs-${id}`,
  name: `FS ${id}`,
  description: '',
  fields: [],
  order,
});

const taskFs = (apiName: string, order: number): ITaskFieldset => ({ apiName, order });

describe('mergeTaskOutputFlow', () => {
  it('buildMergedTaskOutputRows sorts by order descending with stable tie-break', () => {
    const rows = buildMergedTaskOutputRows(
      [field('a', 0), field('b', 3)],
      [taskFs('fs-10', 1), taskFs('fs-20', 2)],
    );
    expect(rows.map((r) => (r.kind === 'field' ? r.field.apiName : r.apiName))).toEqual(['b', 'fs-20', 'fs-10', 'a']);
  });

  it('normalizeMergedTaskOutputOrders assigns contiguous orders', () => {
    const fields = [field('a', 10), field('b', 5)];
    const rows = buildMergedTaskOutputRows(fields, [taskFs('fs-1', 7)]);
    const { nextFields, fieldsetOrderPatches } = normalizeMergedTaskOutputOrders(rows, fields);
    const byApi = Object.fromEntries(nextFields.map((f) => [f.apiName, f.order]));
    expect(byApi.a).toBe(2);
    expect(byApi.b).toBe(0);
    expect(fieldsetOrderPatches).toContainEqual({ apiName: 'fs-1', order: 1 });
  });

  it('moveMergedRow swaps adjacent items', () => {
    const rows = buildMergedTaskOutputRows([field('a', 1)], []);
    const moved = moveMergedRow(rows, 0, 'down');
    expect(moved.length).toBe(1);
  });

  it('buildRuntimeMergedOutputParts interleaves fields and fieldsets', () => {
    const parts = buildRuntimeMergedOutputParts(
      [field('x', 1), field('y', 3)],
      [fs(9, 2)],
    );
    expect(parts.map((output) => (output.kind === 'fieldset' ? output.data.apiName : output.field.apiName))).toEqual(['y', 'fs-9', 'x']);
  });

  describe('buildRowsWithAddedFieldset', () => {
    it('adds fieldset to rows when it is not already present', () => {
      const rows = buildRowsWithAddedFieldset(
        [field('a', 0)],
        [taskFs('fs-1', 1)],
        'fs-new',
      );
      expect(rows).not.toBeNull();
      const apiNames = rows!.map((r) => (r.kind === 'field' ? r.field.apiName : r.apiName));
      expect(apiNames).toContain('fs-new');
    });

    it('returns null when fieldset with that apiName is already present', () => {
      const result = buildRowsWithAddedFieldset(
        [field('a', 0)],
        [taskFs('fs-1', 1)],
        'fs-1',
      );
      expect(result).toBeNull();
    });
  });

  describe('buildRowsWithRemovedFieldset', () => {
    it('removes fieldset by apiName, other rows are preserved', () => {
      const rows = buildRowsWithRemovedFieldset(
        [field('a', 0)],
        [taskFs('fs-1', 1), taskFs('fs-2', 2)],
        'fs-1',
      );
      const apiNames = rows.map((r) => (r.kind === 'field' ? r.field.apiName : r.apiName));
      expect(apiNames).not.toContain('fs-1');
      expect(apiNames).toContain('fs-2');
      expect(apiNames).toContain('a');
    });

    it('does not throw when fieldset is absent — returns rows unchanged', () => {
      const rows = buildRowsWithRemovedFieldset(
        [field('a', 0)],
        [taskFs('fs-1', 1)],
        'fs-missing',
      );
      const apiNames = rows.map((r) => (r.kind === 'field' ? r.field.apiName : r.apiName));
      expect(apiNames).toContain('fs-1');
      expect(apiNames).toContain('a');
    });
  });

  it('normalizeMergedTaskOutputOrders with empty rowsInDisplayOrder returns fields unchanged and empty patches', () => {
    const originalFields = [field('a', 5), field('b', 3)];
    const { nextFields, fieldsetOrderPatches } = normalizeMergedTaskOutputOrders([], originalFields);
    expect(fieldsetOrderPatches).toEqual([]);
    expect(nextFields).toEqual(originalFields);
  });
});
