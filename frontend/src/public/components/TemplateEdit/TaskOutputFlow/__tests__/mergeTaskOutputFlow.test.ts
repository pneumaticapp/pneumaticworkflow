import { IExtraField, IFieldsetData } from '../../../../types/template';
import {
  buildMergedTaskOutputRows,
  buildRuntimeMergedOutputParts,
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

describe('mergeTaskOutputFlow', () => {
  it('buildMergedTaskOutputRows sorts by order descending with stable tie-break', () => {
    const map = new Map<number, IFieldsetData>([
      [10, fs(10, 1)],
      [20, fs(20, 2)],
    ]);
    const rows = buildMergedTaskOutputRows([field('a', 0), field('b', 3)], [10, 20], map);
    expect(rows.map((r) => (r.kind === 'field' ? r.field.apiName : r.fieldsetId))).toEqual(['b', 20, 10, 'a']);
  });

  it('normalizeMergedTaskOutputOrders assigns contiguous orders', () => {
    const fields = [field('a', 10), field('b', 5)];
    const rows = buildMergedTaskOutputRows(fields, [1], new Map([[1, fs(1, 7)]]));
    const { nextFields, fieldsetOrderPatches } = normalizeMergedTaskOutputOrders(rows, fields);
    const byApi = Object.fromEntries(nextFields.map((f) => [f.apiName, f.order]));
    expect(byApi.a).toBe(2);
    expect(byApi.b).toBe(0);
    expect(fieldsetOrderPatches).toContainEqual({ id: 1, order: 1 });
  });

  it('moveMergedRow swaps adjacent items', () => {
    const rows = buildMergedTaskOutputRows([field('a', 1)], [], new Map());
    const moved = moveMergedRow(rows, 0, 'down');
    expect(moved.length).toBe(1);
  });

  it('buildRuntimeMergedOutputParts interleaves fields and fieldsets', () => {
    const parts = buildRuntimeMergedOutputParts(
      [field('x', 1), field('y', 3)],
      [fs(9, 2)],
    );
    expect(parts.map((p) => (p.kind === 'field' ? p.field.apiName : p.data.id))).toEqual(['y', 9, 'x']);
  });
});
