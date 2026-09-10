import { IntlShape } from 'react-intl';

import { EExtraFieldType, IExtraField } from '../../../../types/template';
import { EMoveDirections } from '../../../../types/workflow';
import { getEmptyField } from '../../../TemplateEdit/KickoffRedux/utils/getEmptyField';
import { getEditedFields } from '../../../TemplateEdit/ExtraFields/utils/getEditedFields';
import { getNormalizeFieldsOrders, moveWorkflowField } from '../../../../utils/workflows';
import { getFieldsWithFilteredRulesets } from '../utils';

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

export function deleteField(sortedFields: IExtraField[], apiName: string): IExtraField[] {
  return getNormalizeFieldsOrders(sortedFields.filter((field) => field.apiName !== apiName));
}

export function deleteFieldWithCleanup(sortedFields: IExtraField[], apiName: string): IExtraField[] {
  const updatedFields = deleteField(sortedFields, apiName);

  return getFieldsWithFilteredRulesets(updatedFields, apiName);
}

export function moveField(
  sortedFields: IExtraField[],
  from: number,
  direction: EMoveDirections,
): IExtraField[] {
  const to = direction === EMoveDirections.Up ? from - 1 : from + 1;

  return moveWorkflowField(from, to, sortedFields);
}
