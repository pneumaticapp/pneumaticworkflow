import { useEffect } from 'react';
import type { TDueDateRulePreposition } from '../../../../../types/template';
import type { TRulePrepositionOption } from '../utils/getRulePrepositionOptions';
import type { TRuleTargetOption } from '../utils/getRuleTargetOptions';

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
