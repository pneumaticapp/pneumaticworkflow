/* eslint-disable */
import { EExtraFieldType, IExtraField, TExtraFieldValue } from '../../../../types/template';
import { getEndOfDayTsp } from '../../../../utils/dateTime';
import { parseMarkdownToFiles } from '../../../../utils/parseMarkdownFiles';

type TFieldDispatchRecord = {
  [key in EExtraFieldType]: (field: IExtraField) => IExtraField | null;
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
      .map(({ apiName, value, type }) => {
        if (type === 'url') {
          return { [apiName as string]: (value as string).replace(new RegExp(' ', 'gi'), '%20') };
        } else if (type === 'date' && typeof value === 'string') {
          return { [apiName as string]: getEndOfDayTsp(value) };
        } else if (type === 'number') {
          return { [apiName as string]: String(value).replace(',', '.') };
        } else {
          return { [apiName as string]: value };
        }
      });
  }

  public normalizeFieldsValuesAsObject() {
    return this.fields
      .filter(({ apiName }) => apiName)
      .reduce(
        (acc, { apiName, value, type }) =>
          Object.assign(acc, {
            [apiName]: type === 'url' ? (value as string).replace(new RegExp(' ', 'gi'), '%20') : value,
          }),
        {},
      );
  }

  public getFieldsWithValues() {
    return this.fields
      .map((field) => {
        const renderField = this.fieldValuesDispatch[field.type];

        if (!renderField) {
          return null;
        }

        return renderField(field);
      })
      .filter(Boolean) as IExtraField[];
  }

  private getStorageField = (fieldApiName: string) => {
    if (!this.storageOutput) {
      return null;
    }

    return this.storageOutput.find((field) => field.apiName === fieldApiName);
  };

  private hasServerValue = (field: IExtraField): boolean => {
    if (field.type === EExtraFieldType.File) {
      return Boolean(field.markdownValue) || Boolean(field.attachments?.length);
    }

    if (field.type === EExtraFieldType.User) {
      return Boolean(field.userId || field.groupId);
    }

    if (field.type === EExtraFieldType.Checkbox) {
      return Array.isArray(field.value) && field.value.length > 0;
    }

    return Boolean(field.value);
  };

  private getFieldValue = (
    initialValue: TExtraFieldValue | undefined,
    defaultValue: TExtraFieldValue,
    fieldApiName: string,
    field: IExtraField,
  ) => {
    const normalizedInitialValue = Array.isArray(initialValue) && initialValue.length === 0 ? null : initialValue;
    const storageValue = this.getStorageField(fieldApiName)?.value;

    if (this.hasServerValue(field)) {
      return normalizedInitialValue ?? defaultValue;
    }

    return storageValue ?? normalizedInitialValue ?? defaultValue;
  };

  private fieldValuesDispatch: TFieldDispatchRecord = {
    [EExtraFieldType.Number]: (field: IExtraField) => {
      return { ...field, value: this.getFieldValue(field.value, '', field.apiName, field) };
    },
    [EExtraFieldType.Text]: (field: IExtraField) => {
      return { ...field, value: this.getFieldValue(field.value, '', field.apiName, field) };
    },
    [EExtraFieldType.String]: (field: IExtraField) => {
      return { ...field, value: this.getFieldValue(field.value, '', field.apiName, field) };
    },
    [EExtraFieldType.Url]: (field: IExtraField) => {
      return { ...field, value: this.getFieldValue(field.value, '', field.apiName, field) };
    },
    [EExtraFieldType.File]: (field: IExtraField) => {
      const serverAttachments = parseMarkdownToFiles(field.markdownValue);
      const initialAttachments = serverAttachments.length > 0 ? serverAttachments : null;
      const storageAttachments = this.getStorageField(field.apiName)?.attachments?.filter(
        ({ isRemoved }) => !isRemoved,
      );
      const attachments = this.hasServerValue(field)
        ? initialAttachments || []
        : storageAttachments || initialAttachments || [];
      const value = attachments.map(({ name, url }) => `[${name}](${url})`);

      return {
        ...field,
        attachments,
        value,
      };
    },
    [EExtraFieldType.Date]: (field: IExtraField) => {
      return { ...field, value: this.getFieldValue(field.value, '', field.apiName, field) };
    },
    [EExtraFieldType.Checkbox]: (field: IExtraField) => {
      return { ...field, value: this.getFieldValue(field.value, [], field.apiName, field) };
    },
    [EExtraFieldType.Radio]: (field: IExtraField) => {
      if (!field.selections || field.selections.length === 0) {
        return null;
      }
      return { ...field, value: this.getFieldValue(field.value, null, field.apiName, field) };
    },

    [EExtraFieldType.Creatable]: (field: IExtraField) => {
      if (!field.selections || field.selections.length === 0) {
        return null;
      }

      return { ...field, value: this.getFieldValue(field.value, null, field.apiName, field) };
    },

    [EExtraFieldType.User]: (field: IExtraField) => {
      return { ...field, value: this.getFieldValue(field.value, '', field.apiName, field) };
    },
  };
}
