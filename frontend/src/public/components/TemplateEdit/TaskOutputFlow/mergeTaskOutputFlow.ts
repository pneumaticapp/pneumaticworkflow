import { IExtraField, IFieldsetData, ITaskFieldset } from '../../../types/template';

export type TMergedTaskOutputRow =
  | { kind: 'field'; field: IExtraField }
  | { kind: 'fieldset'; apiName: string; order: number };

function rowOrder(row: TMergedTaskOutputRow): number {
  return row.kind === 'field' ? row.field.order : row.order;
}

export function buildMergedTaskOutputRows(
  fields: IExtraField[],
  fieldsets: ITaskFieldset[],
): TMergedTaskOutputRow[] {
  const rows: TMergedTaskOutputRow[] = [
    ...fields.map((field) => ({ kind: 'field' as const, field })),
    ...fieldsets.map(({apiName, order}) => {
      return {
        kind: 'fieldset' as const,
        apiName,
        order,
      };
    }),
  ];
  return rows.sort((a, b) => {
    const delta = rowOrder(b) - rowOrder(a);
    if (delta !== 0) {
      return delta;
    }
    if (a.kind === 'fieldset' && b.kind === 'fieldset') {
      return b.apiName.localeCompare(a.apiName);
    }
    if (a.kind === 'field' && b.kind === 'field') {
      return b.field.apiName.localeCompare(a.field.apiName);
    }
    return a.kind === 'fieldset' ? 1 : -1;
  });
}

export interface INormalizeMergedTaskOutputResult {
  nextFields: IExtraField[];
  fieldsetOrderPatches: { apiName: string; order: number }[];
}

export function normalizeMergedTaskOutputOrders(
  rowsInDisplayOrder: TMergedTaskOutputRow[],
  allTaskFields: IExtraField[],
): INormalizeMergedTaskOutputResult {
  if (rowsInDisplayOrder.length === 0) {
    return { nextFields: [...allTaskFields], fieldsetOrderPatches: [] };
  }
  const total = rowsInDisplayOrder.length;
  const orderByFieldApiName = new Map<string, number>();
  const fieldsetOrderPatches: { apiName: string; order: number }[] = [];

  rowsInDisplayOrder.forEach((row, index) => {
    const order = total - index - 1;
    if (row.kind === 'field') {
      orderByFieldApiName.set(row.field.apiName, order);
    } else {
      fieldsetOrderPatches.push({ apiName: row.apiName, order });
    }
  });

  const nextFields = allTaskFields.map((field) => ({
    ...field,
    order: orderByFieldApiName.get(field.apiName) ?? field.order,
  }));

  return { nextFields, fieldsetOrderPatches };
}

export type TRuntimeMergedOutputPart =
  | { kind: 'field'; field: IExtraField }
  | { kind: 'fieldset'; data: IFieldsetData };

function runtimeOrder(part: TRuntimeMergedOutputPart): number {
  return part.kind === 'field' ? part.field.order : part.data.order ?? 0;
}

export function buildRuntimeMergedOutputParts(
  output: IExtraField[],
  fieldsets: IFieldsetData[] | undefined,
): TRuntimeMergedOutputPart[] {
  const rows: TRuntimeMergedOutputPart[] = [
    ...output.map((field) => ({ kind: 'field' as const, field })),
    ...(fieldsets || []).map((data) => ({ kind: 'fieldset' as const, data })),
  ];
  return rows.sort((a, b) => {
    const delta = runtimeOrder(b) - runtimeOrder(a);
    if (delta !== 0) {
      return delta;
    }
    if (a.kind === 'fieldset' && b.kind === 'fieldset') {
      return b.data.id - a.data.id;
    }
    if (a.kind === 'field' && b.kind === 'field') {
      return b.field.apiName.localeCompare(a.field.apiName);
    }
    return a.kind === 'fieldset' ? 1 : -1;
  });
}

export function moveMergedRow(
  rows: TMergedTaskOutputRow[],
  index: number,
  direction: 'up' | 'down',
): TMergedTaskOutputRow[] {
  const copy = [...rows];
  const to = direction === 'up' ? index - 1 : index + 1;
  if (to < 0 || to >= copy.length) {
    return copy;
  }
  const tmp = copy[index];
  copy[index] = copy[to];
  copy[to] = tmp;
  return copy;
}
