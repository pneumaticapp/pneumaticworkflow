import { useState, useMemo } from 'react';

import { IExtraField } from '../../../types/template';
import { IFieldRuleSet } from '../../../types/fieldset';
import { saveFieldRuleset, deleteFieldRuleset } from './utils';

export function useFieldRuleModal(
  fields: IExtraField[],
  onFieldsChange: (fields: IExtraField[]) => void,
) {
  const [activeFieldApiName, setActiveFieldApiName] = useState<string | null>(null);
  const [activeFieldRuleset, setActiveFieldRuleset] = useState<IFieldRuleSet | null>(null);

  const openFieldRule = (fieldApiName: string, ruleset?: IFieldRuleSet) => {
    setActiveFieldApiName(fieldApiName);
    setActiveFieldRuleset(ruleset || null);
  };

  const handleFieldRuleSave = (ruleset: IFieldRuleSet) => {
    if (!activeFieldApiName) return;
    onFieldsChange(saveFieldRuleset(fields, activeFieldApiName, ruleset));
    setActiveFieldApiName(null);
  };

  const handleFieldRuleClose = () => {
    setActiveFieldApiName(null);
  };

  const handleDeleteFieldRuleset = (fieldApiName: string, rulesetApiName: string) => {
    onFieldsChange(deleteFieldRuleset(fields, fieldApiName, rulesetApiName));
  };

  const fieldRuleShowFieldOptions = useMemo(() => {
    if (!activeFieldApiName || !fields) {
      return [];
    }
    return fields
      .filter((field) => field.apiName !== activeFieldApiName)
      .map(({ apiName, name, type, selections, dataset }) => ({
        apiName,
        name,
        type,
        selections,
        datasetId: dataset,
      }));
  }, [activeFieldApiName, fields]);

  const activeField = useMemo(() => {
    return fields?.find((field) => field.apiName === activeFieldApiName);
  }, [activeFieldApiName, fields]);

  const { type: fieldType, selections, dataset: datasetId } = activeField ?? {};

  return {
    openFieldRule,
    handleDeleteFieldRuleset,
    fieldRuleModalProps: {
      isOpen: Boolean(activeFieldApiName),
      ruleset: activeFieldRuleset,
      fieldType,
      selections,
      datasetId,
      fieldRuleShowFieldOptions,
      onSave: handleFieldRuleSave,
      onClose: handleFieldRuleClose,
    },
  };
}
