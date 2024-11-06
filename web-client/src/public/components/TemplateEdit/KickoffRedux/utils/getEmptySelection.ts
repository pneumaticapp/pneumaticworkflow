/* eslint-disable */
/* prettier-ignore */
import { IExtraFieldSelection } from '../../../../types/template';
import { createFieldSelectionApiName } from '../../../../utils/createId';

export function getEmptySelection(): IExtraFieldSelection {
  return {
    value: 'New option',
    apiName: createFieldSelectionApiName(),
  };
}
