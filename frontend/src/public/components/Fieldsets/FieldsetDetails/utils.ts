import { IExtraField } from '../../../types/template';
import { IFieldRuleSet } from '../../../types/fieldset';

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
