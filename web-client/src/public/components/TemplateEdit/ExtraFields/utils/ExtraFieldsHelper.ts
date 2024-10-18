/* eslint-disable */
/* prettier-ignore */
import { EExtraFieldType, IExtraField, TExtraFieldValue } from '../../../../types/template';
import { isArrayWithItems } from '../../../../utils/helpers';

type TFieldDispatchRecord = {
  [key in EExtraFieldType]:
  (field: IExtraField) => IExtraField | null;
};

export class ExtraFieldsHelper {
  private fields: IExtraField[];
  private storageOutput?: IExtraField[];

  public constructor(fields: IExtraField[], storageOutput?: IExtraField[]) {
    this.fields = fields;
    this.storageOutput = storageOutput;
  }

  public normalizeFieldsValues() {
    return this.fields
      .filter(({ apiName }) => apiName)
      .map(({ apiName, value, type }) => ({
        [apiName as string]: type === 'url' ? (value as string).replace(new RegExp(' ', 'gi'), '%20') : value,
      }));
  }

  public normalizeFieldsValuesAsObject() {
    return this.fields
      .filter(({ apiName }) => apiName)
      .reduce((acc, { apiName, value, type }) =>
        Object.assign(acc, {
          [apiName]: type === 'url' ? (value as string).replace(new RegExp(' ', 'gi'), '%20') : value,
        }), {});
  }

  public getFieldsWithValues() {
    return this.fields.map(field => {
      const renderField = this.fieldValuesDispatch[field.type];

      if (!renderField) {
        return null;
      }

      return renderField(field);
    }).filter(Boolean) as IExtraField[];
  }

  private getStorageField = (fieldApiName: string) => {
    if (!this.storageOutput) {
      return null;
    }

    return this.storageOutput.find(field => field.apiName === fieldApiName);
  };

  private getFieldValue = (
    initialValue: TExtraFieldValue | undefined,
    defaultValue: TExtraFieldValue,
    fieldApiName: string,
  ) => {
    const normalizedInitialValue = Array.isArray(initialValue) && initialValue.length === 0 ? null : initialValue;

    return this.getStorageField(fieldApiName)?.value || normalizedInitialValue || defaultValue;
  };

  private fieldValuesDispatch: TFieldDispatchRecord = {
    [EExtraFieldType.Text]: (field: IExtraField) => {
      return { ...field, value: this.getFieldValue(field.value, '', field.apiName) };
    },
    [EExtraFieldType.String]: (field: IExtraField) => {
      return { ...field, value: this.getFieldValue(field.value, '', field.apiName) };
    },
    [EExtraFieldType.Url]: (field: IExtraField) => {
      return { ...field, value: this.getFieldValue(field.value, '', field.apiName) };
    },
    [EExtraFieldType.File]: (field: IExtraField) => {
      const isNoInitialAttachments = Array.isArray(field.attachments) && field.attachments.length === 0;
      const initialAttachments = isNoInitialAttachments
        ? null
        : field.attachments?.filter(({ isRemoved }) => !isRemoved);
      const storageAttachments = this.getStorageField(field.apiName)
        ?.attachments?.filter(({ isRemoved }) => !isRemoved);
      const attachments =  storageAttachments || initialAttachments || [];
      const value = attachments.map(({ id }) => String(id));

      return {
        ...field,
        attachments,
        value,
      };
    },
    [EExtraFieldType.Date]: (field: IExtraField) => {
      return { ...field, value: this.getFieldValue(field.value, '', field.apiName) };
    },
    [EExtraFieldType.Checkbox]: (field: IExtraField) => {
      const initialValue = field.selections!.filter(({ isSelected }) => isSelected).map(({ apiName }) => apiName);

      return { ...field, value: this.getFieldValue(initialValue, [], field.apiName) };
    },
    [EExtraFieldType.Radio]: (field: IExtraField) => {
      if (!isArrayWithItems(field.selections)) {
        return null;
      }

      const selectedOption = field.selections.find(({ isSelected }) => isSelected);
      const initialValue = selectedOption ? selectedOption.apiName : null;

      return { ...field, value: this.getFieldValue(initialValue, null, field.apiName) };
    },

    [EExtraFieldType.Creatable]: (field: IExtraField) => {
      if (!isArrayWithItems(field.selections)) {
        return null;
      }

      const selectedOption = field.selections.find(({ isSelected }) => isSelected);
      const initialValue = selectedOption ? String(selectedOption.id) : null;

      return { ...field, value: this.getFieldValue(initialValue, null, field.apiName) };
    },

    [EExtraFieldType.User]: (field: IExtraField) => {
      return { ...field, value: this.getFieldValue(field.value, '', field.apiName) };
    },
  };
}
