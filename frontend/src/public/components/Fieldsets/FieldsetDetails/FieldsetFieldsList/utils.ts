import { IntlShape } from 'react-intl';

import { EExtraFieldType, IExtraField } from '../../../../types/template';
import { EMoveDirections } from '../../../../types/workflow';
import { getEmptyField } from '../../../TemplateEdit/KickoffRedux/utils/getEmptyField';
import { getEditedFields } from '../../../TemplateEdit/ExtraFields/utils/getEditedFields';
import { getNormalizeFieldsOrders, moveWorkflowField } from '../../../../utils/workflows';

export function getSortedFields(fields: IExtraField[]): IExtraField[] {
  return [...fields].sort((a, b) => b.order - a.order);
}

export function createField(
  fields: IExtraField[],
  type: EExtraFieldType,
  formatMessage: IntlShape['formatMessage'],
): IExtraField[] {
  return getNormalizeFieldsOrders([...fields, getEmptyField(type, formatMessage)]);
}

export function editField(
  sortedFields: IExtraField[],
  apiName: string,
  changedProps: Partial<IExtraField>,
): IExtraField[] {
  return getEditedFields(sortedFields, apiName, changedProps);
}

export function deleteField(sortedFields: IExtraField[], index: number): IExtraField[] {
  return getNormalizeFieldsOrders(sortedFields.filter((_, i) => i !== index));
}

export function moveField(
  sortedFields: IExtraField[],
  from: number,
  direction: EMoveDirections,
): IExtraField[] {
  const to = direction === EMoveDirections.Up ? from - 1 : from + 1;

  return moveWorkflowField(from, to, sortedFields);
}
