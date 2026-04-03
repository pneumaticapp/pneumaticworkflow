import { Dispatch, SetStateAction } from 'react';
import { IExtraFieldSelection } from '../../../../types/template';
import { getSelectionDuplicateError } from '../../../../utils/validators';

export const handleSelectionBlur = (
  setDuplicateErrors: Dispatch<SetStateAction<Record<number, string>>>,
  selections?: IExtraFieldSelection[],
) => (optionIndex: number) => () => {
  const value = selections?.[optionIndex]?.value || '';
  const allValues = selections?.map((selection) => selection.value) || [];
  const error = getSelectionDuplicateError(value, allValues);
  if (error) {
    setDuplicateErrors((prev) => ({ ...prev, [optionIndex]: error }));
  }
};
