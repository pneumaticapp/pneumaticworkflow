import { IExtraField } from '../../../../types/template';

export const getEditedFields = (
  initialFields: IExtraField[],
  editedFieldApiName: string,
  changedProps: Partial<IExtraField>,
): IExtraField[] => {
  const newFields = initialFields.map(field => {
    if (field.apiName !== editedFieldApiName) {
      return field;
    }

    return { ...field, ...changedProps };
  });

  return newFields;
};
