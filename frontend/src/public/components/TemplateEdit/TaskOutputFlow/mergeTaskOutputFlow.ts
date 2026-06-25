import { IExtraField, IFieldsetData, TRuntimeMergedOutputPart, TTemplateFieldFieldset } from '../../../types/template';
import { IFieldsetCatalogItem, IFieldsetBindingClient } from '../../../types/fieldset';
import { createFieldsetBindingApiName } from '../../../utils/createId';

export type TMergedTaskOutputRow =
  | { kind: 'field'; field: IExtraField }
  | (IFieldsetBindingClient & { kind: 'fieldset' });

function rowOrder(row: TMergedTaskOutputRow): number {
  return row.kind === 'field' ? row.field.order : row.order;
}

export function buildMergedTaskOutputRows(
  fields: IExtraField[],
  fieldsets: IFieldsetBindingClient[],
): TMergedTaskOutputRow[] {
  const rows: TMergedTaskOutputRow[] = [
    ...fields.map((field) => ({ kind: 'field' as const, field })),
    ...fieldsets.map((fieldset) => ({ ...fieldset, kind: 'fieldset' as const })),
  ];
  return rows.sort((a, b) => {
    const delta = rowOrder(b) - rowOrder(a);
    if (delta !== 0) {
      return delta;
    }
    if (a.kind === 'fieldset' && b.kind === 'fieldset') {
      return b.apiNameBinding!.localeCompare(a.apiNameBinding!);
    }
    if (a.kind === 'field' && b.kind === 'field') {
      return b.field.apiName.localeCompare(a.field.apiName);
    }
    return a.kind === 'fieldset' ? 1 : -1;
  });
}

export interface INormalizeMergedTaskOutputResult {
  nextFields: IExtraField[];
  nextFieldsets: IFieldsetBindingClient[];
}

export function normalizeMergedTaskOutputOrders(
  rowsInDisplayOrder: TMergedTaskOutputRow[],
  allTaskFields: IExtraField[],
): INormalizeMergedTaskOutputResult {
  if (rowsInDisplayOrder.length === 0) {
    return { nextFields: [...allTaskFields], nextFieldsets: [] };
  }
  const total = rowsInDisplayOrder.length;
  const orderByFieldApiName = new Map<string, number>();
  const nextFieldsets: IFieldsetBindingClient[] = [];

  rowsInDisplayOrder.forEach((row, index) => {
    const order = total - index - 1;
    if (row.kind === 'field') {
      orderByFieldApiName.set(row.field.apiName, order);
    } else {
      const { kind, ...fieldsetBinding } = row;
      nextFieldsets.push({ ...fieldsetBinding, order });
    }
  });

  const nextFields = allTaskFields.map((field) => ({
    ...field,
    order: orderByFieldApiName.get(field.apiName) ?? field.order,
  }));

  return { nextFields, nextFieldsets };
}

function runtimeOrder(part: TRuntimeMergedOutputPart): number {
  if (part.kind === 'fieldset') return part.data.order ?? 0;
  if (part.kind === 'field') return part.field.order;

  return 0;
}

export function buildRuntimeMergedOutputParts(
  output: IExtraField[],
  fieldsets: IFieldsetData[] | TTemplateFieldFieldset[] | undefined,
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
      return b.data.apiName.localeCompare(a.data.apiName);
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

export function buildRowsWithAddedFieldset(
  fields: IExtraField[],
  fieldsets: IFieldsetBindingClient[],
  newFieldsetBinding: IFieldsetBindingClient,
): TMergedTaskOutputRow[] | null {
  if (fieldsets.some((fieldset) => fieldset.sharedFieldsetId === newFieldsetBinding.sharedFieldsetId)) {
    return null;
  }
  const nextFieldsets = [...fieldsets, newFieldsetBinding];
  return buildMergedTaskOutputRows(fields, nextFieldsets);
}

export function buildRowsWithRemovedFieldset(
  fields: IExtraField[],
  fieldsets: IFieldsetBindingClient[],
  fieldsetApiName: string,
): TMergedTaskOutputRow[] {
  const nextFieldsets = fieldsets.filter((fieldset) => fieldset.apiName !== fieldsetApiName);
  return buildMergedTaskOutputRows(fields, nextFieldsets);
}

export function createFieldsetBinding(catalogItem: IFieldsetCatalogItem): IFieldsetBindingClient {
  const apiNameBinding = createFieldsetBindingApiName();

  return {
    sharedFieldsetId: catalogItem.id,
    apiName: apiNameBinding,
    apiNameBinding,
    name: catalogItem.name,
    title: catalogItem.title,
    description: catalogItem.description,
    order: -1,
    labelPosition: catalogItem.labelPosition,
    layout: catalogItem.layout,
    rules: catalogItem.rules,
    fields: catalogItem.fields,
  };
}
