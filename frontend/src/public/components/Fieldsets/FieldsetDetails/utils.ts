import type { Dispatch } from 'redux';
import type { IExtraField } from '../../../types/template';
import type {
  IFieldRuleSet,
  IFieldRuleShowGroupAnd,
  IFieldsetRuleSet,
  IUpdateFieldsetParams,
  IFieldsetCatalogItem,
} from '../../../types/fieldset';
import { EFieldRuleType } from '../../../types/fieldset';
import { deepCopy, isObjectChanged } from '../../../utils/helpers';
import { getNormalizeFieldsOrders, sortFieldsByOrder } from '../../../utils/workflows';
import { validateFieldsetTitle } from '../../../utils/validators';
import { validateFieldsetRules } from '../validators';
import { normalizeFieldsForUI } from './fieldsetFieldMappers';
import { NotificationManager } from '../../UI/Notifications';
import { cloneFieldsetAction, updateFieldsetAction } from '../../../redux/fieldsets/slice';
import { FIELDSET_CHANGE_KEYS } from './constants';
import type { TLocalFieldsetState, TFieldsetChanges } from './types';

export function saveFieldRuleset(fields: IExtraField[], fieldApiName: string, ruleset: IFieldRuleSet): IExtraField[] {
  return fields.map((field) => {
    if (field.apiName !== fieldApiName) return field;

    const isExistingRuleset = (field.rulesets || []).some(
      (existingRuleset) => existingRuleset.apiName === ruleset.apiName,
    );
    const updatedRulesets = isExistingRuleset
      ? (field.rulesets || []).map((existingRuleset) =>
          existingRuleset.apiName === ruleset.apiName ? ruleset : existingRuleset,
        )
      : [...(field.rulesets || []), ruleset];

    return { ...field, rulesets: updatedRulesets };
  });
}

export function deleteFieldRuleset(fields: IExtraField[], fieldApiName: string, rulesetApiName: string): IExtraField[] {
  return fields.map((field) => {
    if (field.apiName !== fieldApiName) return field;

    const updatedRulesets = (field.rulesets || []).filter((ruleset) => ruleset.apiName !== rulesetApiName);

    return { ...field, rulesets: updatedRulesets };
  });
}

export function getFieldsWithFilteredRulesets(fields: IExtraField[], deletedFieldApiName: string): IExtraField[] {
  return fields.map((field) => {
    if (!field.rulesets?.length) return field;

    const filteredRulesets = field.rulesets.filter((ruleset) => {
      if (ruleset.type !== EFieldRuleType.Show) return true;

      return ruleset.groupsOr.every((groupOr) =>
        groupOr.groupsAnd.every((groupAnd: IFieldRuleShowGroupAnd) => groupAnd.field !== deletedFieldApiName),
      );
    });

    if (filteredRulesets.length === field.rulesets.length) return field;

    return { ...field, rulesets: filteredRulesets };
  });
}

export const initLocalFieldset = (fieldset: IFieldsetCatalogItem): TLocalFieldsetState => ({
  title: fieldset.title,
  description: fieldset.description || '',
  labelPosition: fieldset.labelPosition,
  fields: normalizeFieldsForUI(fieldset.fields as unknown as IExtraField[]),
  rulesets: fieldset.rulesets || [],
});

export const checkIsTitleError = (title: string, hasTitleChanged: boolean): boolean =>
  (hasTitleChanged || Boolean(title)) && Boolean(validateFieldsetTitle(title));

const isFieldsetPropertyChanged = (
  key: keyof TLocalFieldsetState,
  initialFieldset: TLocalFieldsetState,
  localFieldset: TLocalFieldsetState,
): boolean => {
  if (initialFieldset[key] === localFieldset[key]) {
    return false;
  }

  const normalizeRuleset = (ruleset: IFieldsetRuleSet | IFieldRuleSet) => ({
    ...ruleset,
    message: ruleset.message || '',
    ...('fields' in ruleset && { fields: [...ruleset.fields].sort() }),
    groupsOr: ruleset.groupsOr.map(({ groupsAnd }) => groupsAnd),
  });

  if (key === 'fields') {
    const normalizeFields = (fields: IExtraField[]) =>
      deepCopy(
        getNormalizeFieldsOrders(sortFieldsByOrder(fields)).map((field) => ({
          ...field,
          selections: field.selections?.length ? field.selections : [],
          rulesets: (field.rulesets || []).map(normalizeRuleset),
        })),
      );

    return isObjectChanged(normalizeFields(initialFieldset.fields), normalizeFields(localFieldset.fields));
  }

  if (key === 'rulesets') {
    const normalizeRulesets = (rulesets: IFieldsetRuleSet[]) => deepCopy(rulesets.map(normalizeRuleset));

    return isObjectChanged(normalizeRulesets(initialFieldset.rulesets), normalizeRulesets(localFieldset.rulesets));
  }

  return true;
};

export const getFieldsetChanges = (
  initialFieldset: TLocalFieldsetState,
  localFieldset: TLocalFieldsetState,
): TFieldsetChanges => {
  const changes: TFieldsetChanges = {};

  FIELDSET_CHANGE_KEYS.forEach((key) => {
    if (!isFieldsetPropertyChanged(key, initialFieldset, localFieldset)) return;

    switch (key) {
      case 'title':
        changes.title = localFieldset.title;
        break;
      case 'description':
        changes.description = localFieldset.description;
        break;
      case 'labelPosition':
        changes.labelPosition = localFieldset.labelPosition;
        break;
      case 'fields':
        changes.fields = localFieldset.fields;
        break;
      case 'rulesets':
        changes.rulesets = localFieldset.rulesets;
        break;
    }
  });

  return changes;
};

export const saveFieldset = ({
  fieldset,
  isChanged,
  localFieldset,
  fieldsetChanges,
  dispatch,
  formatMessage,
  onSuccess,
}: {
  fieldset: IFieldsetCatalogItem | null;
  isChanged: boolean;
  localFieldset: TLocalFieldsetState;
  fieldsetChanges: TFieldsetChanges;
  dispatch: Dispatch;
  formatMessage: (descriptor: { id: string }) => string;
  onSuccess?: () => void;
}): void => {
  if (!fieldset || !isChanged) return;

  const titleErrorMessageKey = validateFieldsetTitle(localFieldset.title);

  if (titleErrorMessageKey) {
    NotificationManager.warning({
      message: formatMessage({ id: titleErrorMessageKey }),
    });
    return;
  }

  if (fieldsetChanges.rulesets) {
    const ruleErrorMessageKey = validateFieldsetRules(fieldsetChanges.rulesets, localFieldset.fields);

    if (ruleErrorMessageKey) {
      NotificationManager.warning({
        message: formatMessage({ id: ruleErrorMessageKey }),
      });
      return;
    }
  }

  const payload: IUpdateFieldsetParams = {
    id: fieldset.id,
    onSuccess,
  };

  if (fieldsetChanges.title !== undefined) {
    payload.title = fieldsetChanges.title;
  }
  if (fieldsetChanges.description !== undefined) {
    payload.description = fieldsetChanges.description;
  }
  if (fieldsetChanges.labelPosition) {
    payload.labelPosition = fieldsetChanges.labelPosition;
  }
  if (fieldsetChanges.fields) {
    payload.fields = fieldsetChanges.fields.map(({ id: _id, ...rest }) => rest) as IUpdateFieldsetParams['fields'];
  }
  if (fieldsetChanges.rulesets) {
    payload.rulesets = fieldsetChanges.rulesets;
  }

  dispatch(updateFieldsetAction(payload));
};

export const cloneFieldset = ({
  fieldsetId,
  isChanged,
  dispatch,
  formatMessage,
}: {
  fieldsetId: number;
  isChanged: boolean;
  dispatch: Dispatch;
  formatMessage: (descriptor: { id: string }) => string;
}): void => {
  if (isChanged) {
    NotificationManager.warning({
      message: formatMessage({ id: 'fieldsets.clone-unsaved-warning' }),
    });
    return;
  }
  dispatch(cloneFieldsetAction({ id: fieldsetId }));
};
