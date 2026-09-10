import { SetStateAction } from 'react';
import { Dispatch } from 'redux';
import { IExtraField } from '../../../types/template';
import {
  IFieldRuleSet,
  EFieldRuleType,
  IUpdateFieldsetParams,
  IFieldsetCatalogItem,
} from '../../../types/fieldset';
import { validateFieldsetTitle } from '../../../utils/validators';
import { validateFieldsetRules } from '../validators';
import { normalizeFieldsForUI } from './fieldsetFieldMappers';
import { NotificationManager } from '../../UI/Notifications';
import { cloneFieldsetAction, updateFieldsetAction } from '../../../redux/fieldsets/slice';
import { TLocalFieldsetState, TFieldsetChanges } from './types';

export function saveFieldRuleset(
  fields: IExtraField[],
  fieldApiName: string,
  ruleset: IFieldRuleSet,
): IExtraField[] {
  return fields.map((field) => {
    if (field.apiName !== fieldApiName) return field;

    const isExistingRuleset = (field.rulesets || []).some(
      (existingRuleset) => existingRuleset.apiName === ruleset.apiName,
    );
    const updatedRulesets = isExistingRuleset
      ? (field.rulesets || []).map(
        (existingRuleset) => existingRuleset.apiName === ruleset.apiName ? ruleset : existingRuleset,
      )
      : [...(field.rulesets || []), ruleset];

    return { ...field, rulesets: updatedRulesets };
  });
}

export function deleteFieldRuleset(
  fields: IExtraField[],
  fieldApiName: string,
  rulesetApiName: string,
): IExtraField[] {
  return fields.map((field) => {
    if (field.apiName !== fieldApiName) return field;

    const updatedRulesets = (field.rulesets || []).filter(
      (ruleset) => ruleset.apiName !== rulesetApiName,
    );

    return { ...field, rulesets: updatedRulesets };
  });
}

export function getFieldsWithFilteredRulesets(
  fields: IExtraField[],
  deletedFieldApiName: string,
): IExtraField[] {
  return fields.map((field) => {
    if (!field.rulesets?.length) return field;

    const filteredRulesets = field.rulesets.filter((ruleset) => {
      if (ruleset.type !== EFieldRuleType.Show) return true;

      return ruleset.groupsOr.every((groupOr) =>
        groupOr.groupsAnd.every((groupAnd) => groupAnd.field !== deletedFieldApiName),
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

export const updateFieldsetProperty = <K extends keyof TLocalFieldsetState>(
  key: K,
  value: TLocalFieldsetState[K],
  setLocalFieldset: (value: SetStateAction<TLocalFieldsetState>) => void,
  setFieldsetChanges: (value: SetStateAction<TFieldsetChanges>) => void,
): void => {
  setLocalFieldset((prev) => ({ ...prev, [key]: value }));
  setFieldsetChanges((prev) => ({ ...prev, [key]: value }));
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
    payload.fields = fieldsetChanges.fields.map(
      ({ id: _id, ...rest }) => rest,
    ) as IUpdateFieldsetParams['fields'];
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
