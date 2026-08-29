import { IExtraField } from '../../../types/template';
import { IFieldRuleSet, EFieldRuleType } from '../../../types/fieldset';

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
