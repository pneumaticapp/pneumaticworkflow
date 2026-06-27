import { makeExtraField } from '../../../../__stubs__/fields.factory';
import { makeFieldsetBindingClient, makeFieldsetData } from '../../../../__stubs__/fieldsets.factory';
import {
  buildMergedTaskOutputRows,
  buildRuntimeMergedOutputParts,
  buildRowsWithAddedFieldset,
  buildRowsWithRemovedFieldset,
  moveMergedRow,
  normalizeMergedTaskOutputOrders,
  TMergedTaskOutputRow,
} from '../mergeTaskOutputFlow';

const assertRowsDefined = (
  rows: TMergedTaskOutputRow[] | null,
): TMergedTaskOutputRow[] => {
  if (rows === null) {
    throw new Error('expected rows to be non-null');
  }
  return rows;
};

const field = (apiName: string, order: number) =>
  makeExtraField({ apiName, name: apiName, order });

const fs = (id: number, order: number) =>
  makeFieldsetData({ sharedFieldsetId: id, apiName: `fs-${id}`, name: `FS ${id}`, order });

describe('mergeTaskOutputFlow', () => {
  it('buildMergedTaskOutputRows sorts by order descending with stable tie-break', () => {
    const rows = buildMergedTaskOutputRows(
      [field('a', 0), field('b', 3)],
      [
        makeFieldsetBindingClient({ apiNameBinding: 'fs-10', order: 1 }),
        makeFieldsetBindingClient({ apiNameBinding: 'fs-20', order: 2 }),
      ],
    );
    expect(rows.map((row) => (row.kind === 'field' ? row.field.apiName : row.apiNameBinding))).toEqual(['b', 'fs-20', 'fs-10', 'a']);
  });

  it('normalizeMergedTaskOutputOrders assigns contiguous orders', () => {
    const fields = [field('a', 10), field('b', 5)];
    const rows = buildMergedTaskOutputRows(fields, [
      makeFieldsetBindingClient({ apiNameBinding: 'fs-1', order: 7 }),
    ]);
    const { nextFields, nextFieldsets } = normalizeMergedTaskOutputOrders(rows, fields);
    const byApi = Object.fromEntries(nextFields.map((f) => [f.apiName, f.order]));
    expect(byApi.a).toBe(2);
    expect(byApi.b).toBe(0);
    expect(nextFieldsets).toContainEqual(expect.objectContaining({ apiNameBinding: 'fs-1', order: 1 }));
  });

  it('moveMergedRow swaps adjacent items and does not mutate the input', () => {
    const original = buildMergedTaskOutputRows(
      [field('a', 4), field('b', 3), field('c', 2), field('d', 1)],
      [],
    );
    const apiNamesOf = (rows: ReturnType<typeof buildMergedTaskOutputRows>) =>
      rows.map((row) => (row.kind === 'field' ? row.field.apiName : row.apiNameBinding));
    const snapshotBefore = apiNamesOf(original);
    expect(snapshotBefore).toEqual(['a', 'b', 'c', 'd']);

    const moved = moveMergedRow(original, 1, 'down');

    expect(apiNamesOf(moved)).toEqual(['a', 'c', 'b', 'd']);
    expect(moved).not.toBe(original);
    expect(apiNamesOf(original)).toEqual(snapshotBefore);
  });

  it('buildRuntimeMergedOutputParts interleaves fields and fieldsets', () => {
    const parts = buildRuntimeMergedOutputParts(
      [field('x', 1), field('y', 3)],
      [fs(9, 2)],
    );
    expect(parts.map((output) => (output.kind === 'fieldset' ? output.data.apiName : output.field.apiName))).toEqual(['y', 'fs-9', 'x']);
  });

  it('buildRuntimeMergedOutputParts returns only fields when fieldsets is undefined', () => {
    const parts = buildRuntimeMergedOutputParts(
      [field('x', 1), field('y', 3)],
      undefined,
    );
    expect(parts.every((p) => p.kind === 'field')).toBe(true);
    expect(parts.map((p) => (p.kind === 'field' ? p.field.apiName : ''))).toEqual(['y', 'x']);
  });

  describe('buildRowsWithAddedFieldset', () => {
    it('adds fieldset to rows when it is not already present', () => {
      const result = buildRowsWithAddedFieldset(
        [field('a', 0)],
        [makeFieldsetBindingClient({ apiNameBinding: 'fs-1', order: 1 })],
        makeFieldsetBindingClient({ apiNameBinding: 'fs-new', order: 0, sharedFieldsetId: 99 }),
      );
      const rows = assertRowsDefined(result);
      const apiNames = rows.map((row) => (row.kind === 'field' ? row.field.apiName : row.apiNameBinding));
      expect(apiNames).toContain('fs-new');
    });

    it('returns null when fieldset with that apiName is already present', () => {
      const result = buildRowsWithAddedFieldset(
        [field('a', 0)],
        [makeFieldsetBindingClient({ apiNameBinding: 'fs-1', order: 1 })],
        makeFieldsetBindingClient({ apiNameBinding: 'fs-1-dup', order: 0, sharedFieldsetId: 1 }),
      );
      expect(result).toBeNull();
    });

    it('places the newly added fieldset as the last row in the merged list', () => {
      const result = buildRowsWithAddedFieldset(
        [field('a', 5), field('b', 3)],
        [makeFieldsetBindingClient({ apiNameBinding: 'fs-1', order: 1 })],
        makeFieldsetBindingClient({ apiNameBinding: 'fs-new', order: 0, sharedFieldsetId: 99 }),
      );
      const rows = assertRowsDefined(result);
      const lastRow = rows[rows.length - 1];
      expect(lastRow.kind).toBe('fieldset');
      expect(lastRow.kind === 'fieldset' && lastRow.apiNameBinding).toBe('fs-new');
    });
  });

  describe('buildRowsWithRemovedFieldset', () => {
    it('removes fieldset by sharedFieldsetId, other rows are preserved', () => {
      const rows = buildRowsWithRemovedFieldset(
        [field('a', 0)],
        [
          makeFieldsetBindingClient({ apiNameBinding: 'fs-1', order: 1 }),
          makeFieldsetBindingClient({ apiNameBinding: 'fs-2', order: 2, sharedFieldsetId: 2 }),
        ],
        1,
      );
      const apiNames = rows.map((row) => (row.kind === 'field' ? row.field.apiName : row.apiNameBinding));
      expect(apiNames).not.toContain('fs-1');
      expect(apiNames).toContain('fs-2');
      expect(apiNames).toContain('a');
    });

    it('does not throw when fieldset is absent — returns rows unchanged', () => {
      const rows = buildRowsWithRemovedFieldset(
        [field('a', 0)],
        [makeFieldsetBindingClient({ apiNameBinding: 'fs-1', order: 1 })],
        999,
      );
      const apiNames = rows.map((row) => (row.kind === 'field' ? row.field.apiName : row.apiNameBinding));
      expect(apiNames).toContain('fs-1');
      expect(apiNames).toContain('a');
    });
  });

  it('normalizeMergedTaskOutputOrders with empty rowsInDisplayOrder returns fields unchanged and empty patches', () => {
    const originalFields = [field('a', 5), field('b', 3)];
    const { nextFields, nextFieldsets } = normalizeMergedTaskOutputOrders([], originalFields);
    expect(nextFieldsets).toEqual([]);
    expect(nextFields).toEqual(originalFields);
  });
});
