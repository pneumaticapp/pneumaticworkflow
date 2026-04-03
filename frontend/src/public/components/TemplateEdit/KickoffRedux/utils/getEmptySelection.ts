/* eslint-disable */
/* prettier-ignore */
import { IExtraFieldSelection } from '../../../../types/template';
import { createFieldSelectionApiName } from '../../../../utils/createId';

export function getEmptySelection(counter?: number): IExtraFieldSelection {
  return {
    value: counter ? `New option ${counter}` : 'New option',
    apiName: createFieldSelectionApiName(),
  };
}
