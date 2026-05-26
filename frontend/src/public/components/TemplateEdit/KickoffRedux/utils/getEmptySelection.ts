/* eslint-disable */
/* prettier-ignore */
import { IExtraFieldSelection } from '../../../../types/template';
import { createFieldSelectionApiName } from '../../../../utils/createId';

const NEW_OPTION_BASE = 'New option';
const NEW_OPTION_REGEX = /^New option (\d+)$/;

export function getEmptySelection(existingSelections?: IExtraFieldSelection[]): IExtraFieldSelection {
  let counter = 1;

  if (existingSelections?.length) {
    let maxNumber = 0;
    existingSelections.forEach((s) => {
      const match = s.value.match(NEW_OPTION_REGEX);
      if (match) {
        maxNumber = Math.max(maxNumber, parseInt(match[1], 10));
      }
    });
    counter = maxNumber + 1;
  }

  return {
    value: `${NEW_OPTION_BASE} ${counter}`,
    apiName: createFieldSelectionApiName(),
  };
}
