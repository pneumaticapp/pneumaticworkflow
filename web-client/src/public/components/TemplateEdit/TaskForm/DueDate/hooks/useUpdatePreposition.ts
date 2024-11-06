import { useEffect } from 'react';
import { TDueDateRulePreposition } from '../../../../../types/template';
import { TRulePrepositionOption } from '../utils/getRulePrepositionOptions';
import { TRuleTargetOption } from '../utils/getRuleTargetOptions';

export function useUpdatePreposition(
  prepositionOptions: TRulePrepositionOption[],
  currentPrepositionOption: TRulePrepositionOption | null,
  currentTargetOption: TRuleTargetOption | null,
  setPrepositionOption: (option: TDueDateRulePreposition) => void,
) {
  useEffect(() => {
    if (!currentPrepositionOption || prepositionOptions.includes(currentPrepositionOption)) {
      return undefined;
    }

    if (prepositionOptions.length === 1) {
      const [option] = prepositionOptions;
      setPrepositionOption(option.rulePreposition);
    }

    return undefined;
  }, [currentTargetOption]);
}
