import type { IFieldRuleShowGroupAnd } from '../types/fieldset';
import { EFieldRuleOperator, EFieldRuleType, EFieldRuleValueType } from '../types/fieldset';
import type { IExtraField } from '../types/template';
import { EExtraFieldType } from '../types/template';

export const checkDependentFieldValue = (
  dependentField: IExtraField,
  operator: EFieldRuleOperator,
  expectedValue: string,
  valueType?: EFieldRuleValueType | null,
): boolean => {
  if (dependentField.type === EExtraFieldType.User) {
    switch (operator) {
      case EFieldRuleOperator.Exist:
      case EFieldRuleOperator.NotExist: {
        const hasValue = Boolean(dependentField.userId || dependentField.groupId);
        return operator === EFieldRuleOperator.Exist ? hasValue : !hasValue;
      }

      case EFieldRuleOperator.Equal:
      case EFieldRuleOperator.NotEqual: {
        const selectedId = valueType === EFieldRuleValueType.Group ? dependentField.groupId : dependentField.userId;
        const isEqual = Boolean(selectedId) && String(selectedId) === expectedValue;
        return operator === EFieldRuleOperator.Equal ? isEqual : !isEqual;
      }

      default:
        return false;
    }
  }

  const { value, attachments } = dependentField;

  switch (operator) {
    case EFieldRuleOperator.Exist:
    case EFieldRuleOperator.NotExist: {
      const hasValue = Boolean(
        attachments?.length || (Array.isArray(value) ? value.length > 0 : Boolean(value && String(value).trim())),
      );
      return operator === EFieldRuleOperator.Exist ? hasValue : !hasValue;
    }

    case EFieldRuleOperator.Equal:
    case EFieldRuleOperator.NotEqual: {
      const isEqual = Array.isArray(value) ? value.length === 1 && value[0] === expectedValue : value === expectedValue;
      return operator === EFieldRuleOperator.Equal ? isEqual : !isEqual;
    }

    case EFieldRuleOperator.Contain:
    case EFieldRuleOperator.NotContain: {
      const isContain = Array.isArray(value)
        ? value.includes(expectedValue)
        : Boolean(value) && String(value).includes(expectedValue);
      return operator === EFieldRuleOperator.Contain ? isContain : !isContain;
    }

    case EFieldRuleOperator.GreaterThan:
      return Boolean(value && String(value).trim()) && Number(value) > Number(expectedValue);

    case EFieldRuleOperator.LessThan:
      return Boolean(value && String(value).trim()) && Number(value) < Number(expectedValue);

    default:
      return false;
  }
};

export const isFieldHidden = (field: IExtraField, fieldsMap: Map<string, IExtraField>): boolean => {
  const showRulesets = field.rulesets?.filter((ruleset) => ruleset.type === EFieldRuleType.Show) ?? [];
  if (showRulesets.length === 0) {
    return Boolean(field.isHidden);
  }

  const hasMatchingShowRuleset = showRulesets.some((ruleset) =>
    ruleset.groupsOr.some((groupOr) =>
      groupOr.groupsAnd.every((groupAnd: IFieldRuleShowGroupAnd) => {
        const dependentField = fieldsMap.get(groupAnd.field);
        if (!dependentField) {
          return false;
        }
        return checkDependentFieldValue(dependentField, groupAnd.operator, groupAnd.value, groupAnd.valueType);
      }),
    ),
  );

  if (hasMatchingShowRuleset) {
    return false;
  }

  return true;
};

const markHiddenFields = <TField extends IExtraField>(fieldList: TField[], fieldsMap: Map<string, IExtraField>) =>
  fieldList.map((field) => ({
    ...field,
    isHidden: isFieldHidden(field, fieldsMap),
  }));

export const updateFieldsHidden = <TField extends IExtraField, TFieldset extends { fields: TField[] }>(
  fields: TField[],
  fieldsets: TFieldset[] = [],
): {
  fields: TField[];
  fieldsets: TFieldset[];
} => {
  const fieldsMap = new Map<string, IExtraField>();
  fields.forEach((field) => fieldsMap.set(field.apiName, field));
  fieldsets.forEach((fieldset) => {
    fieldset.fields.forEach((field) => fieldsMap.set(field.apiName, field));
  });

  return {
    fields: markHiddenFields(fields, fieldsMap),
    fieldsets: fieldsets.map((fieldset) => ({
      ...fieldset,
      fields: markHiddenFields(fieldset.fields, fieldsMap),
    })),
  };
};

export const getVisibleFields = <TField extends IExtraField, TFieldset extends { fields: TField[] }>(
  fields: TField[],
  fieldsets: TFieldset[] = [],
): {
  visibleFields: TField[];
  visibleFieldsets: TFieldset[];
} => {
  return {
    visibleFields: fields.filter((field) => !field.isHidden),
    visibleFieldsets: fieldsets.map((fieldset) => ({
      ...fieldset,
      fields: fieldset.fields.filter((field) => !field.isHidden),
    })),
  };
};

export const getVisibleFieldsByShowRules = <TField extends IExtraField, TFieldset extends { fields: TField[] }>(
  fields: TField[],
  fieldsets: TFieldset[] = [],
) => {
  const { fields: markedFields, fieldsets: markedFieldsets } = updateFieldsHidden(fields, fieldsets);
  return getVisibleFields(markedFields, markedFieldsets);
};
