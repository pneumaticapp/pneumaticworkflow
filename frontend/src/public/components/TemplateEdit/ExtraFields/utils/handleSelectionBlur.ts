import { Dispatch, SetStateAction } from 'react';
import { IExtraFieldSelection } from '../../../../types/template';
import { getSelectionDuplicateError } from '../../../../utils/validators';

export const handleSelectionBlur = (
  setDuplicateErrors: Dispatch<SetStateAction<Record<string, string>>>,
  selections?: IExtraFieldSelection[],
) => (apiName: string) => () => {
  const selection = selections?.find((item) => item.apiName === apiName);
  const value = selection?.value || '';
  const allValues = selections?.map((item) => item.value) || [];
  const error = getSelectionDuplicateError(value, allValues);
  if (error) {
    setDuplicateErrors((prev) => ({ ...prev, [apiName]: error }));
  }
};

export function recalculateDuplicateErrors(selections: IExtraFieldSelection[]): Record<string, string> {
  const errors: Record<string, string> = {};
  const seenValues = new Set<string>();
  const allValues = selections.map((item) => item.value);

  selections.forEach((selection) => {
    const trimmedValue = (selection.value || '').trim().toLowerCase();
    if (!trimmedValue) return;

    if (seenValues.has(trimmedValue)) {
      const error = getSelectionDuplicateError(selection.value, allValues);
      if (error) {
        errors[selection.apiName] = error;
      }
    } else {
      seenValues.add(trimmedValue);
    }
  });

  return errors;
}
