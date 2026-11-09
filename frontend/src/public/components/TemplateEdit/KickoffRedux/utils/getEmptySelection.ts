/* prettier-ignore */
import { IExtraFieldSelection } from '../../../../types/template';
import { createFieldSelectionApiName } from '../../../../utils/createId';

const NEW_OPTION_BASE = 'New option';
export function getEmptySelection(
  existingSelections?: IExtraFieldSelection[],
  label = NEW_OPTION_BASE,
): IExtraFieldSelection {
  const escapedLabel = label.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const newOptionRegex = new RegExp(`^(?:New option|${escapedLabel}) (\\d+)$`);
  let counter = 1;

  if (existingSelections?.length) {
    let maxNumber = 0;
    existingSelections.forEach((s) => {
      const match = s.value.match(newOptionRegex);
      if (match) {
        maxNumber = Math.max(maxNumber, parseInt(match[1], 10));
      }
    });
    counter = maxNumber + 1;
  }

  return {
    value: `${label} ${counter}`,
    apiName: createFieldSelectionApiName(),
  };
}
