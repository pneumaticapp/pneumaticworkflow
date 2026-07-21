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
          return { [apiName as string]: (value as string).replace(/ /gi, '%20') };
        }

        if (type === 'date' && typeof value === 'string') {
          return { [apiName as string]: getEndOfDayTsp(value) };
        }

        if (type === 'number') {
          return { [apiName as string]: String(value).replace(',', '.') };
        }

        return { [apiName as string]: value };
      });
  }

  public normalizeFieldsValuesAsObject() {
    return this.fields
      .filter(({ apiName }) => apiName)
      .reduce(
        (acc, { apiName, value, type }) =>
          Object.assign(acc, {
            [apiName]: type === 'url' ? (value as string).replace(/ /gi, '%20') : value,
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

  private getFieldValue = (
    initialValue: TExtraFieldValue | undefined,
    defaultValue: TExtraFieldValue,
    fieldApiName: string,
  ) => {
    const normalizedInitialValue = initialValue === '' || (Array.isArray(initialValue) && initialValue.length === 0)
      ? null
      : initialValue;
    const storageField = this.getStorageField(fieldApiName);
    const storageValue = storageField?.value;
    const normalizedStorageValue = storageValue === '' || (Array.isArray(storageValue) && storageValue.length === 0)
      ? null
      : storageValue;

    return storageField
      ? normalizedStorageValue ?? defaultValue
      : normalizedInitialValue ?? defaultValue;
  };

  private fieldValuesDispatch: TFieldDispatchRecord = {
    [EExtraFieldType.Number]: (field: IExtraField) => {
      return { ...field, value: this.getFieldValue(field.value, '', field.apiName) };
    },
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
      const serverAttachmentsFromMarkdown = parseMarkdownToFiles(field.markdownValue);
      const serverAttachmentsFromField = field.attachments?.filter(({ isRemoved }) => !isRemoved) ?? [];
      let initialAttachments: IExtraField['attachments'] | null = null;

      if (serverAttachmentsFromMarkdown.length > 0) {
        initialAttachments = serverAttachmentsFromMarkdown;
      } else if (serverAttachmentsFromField.length > 0) {
        initialAttachments = serverAttachmentsFromField;
      }
      const storageField = this.getStorageField(field.apiName);
      const storageAttachments = storageField
        ? storageField.attachments?.filter(({ isRemoved }) => !isRemoved)
          ?? parseMarkdownToFiles(storageField.markdownValue)
        : null;
      const attachments = storageAttachments ?? initialAttachments ?? [];
      const value = attachments.map(({ name, url }) => `[${name}](${url})`);

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
      return { ...field, value: this.getFieldValue(field.value, [], field.apiName) };
    },
    [EExtraFieldType.Radio]: (field: IExtraField) => {
      if (!field.selections || field.selections.length === 0) {
        return null;
      }
      return { ...field, value: this.getFieldValue(field.value, null, field.apiName) };
    },

    [EExtraFieldType.Creatable]: (field: IExtraField) => {
      if (!field.selections || field.selections.length === 0) {
        return null;
      }

      return { ...field, value: this.getFieldValue(field.value, null, field.apiName) };
    },

    [EExtraFieldType.User]: (field: IExtraField) => {
      const storageField = this.getStorageField(field.apiName);

      return {
        ...field,
        value: this.getFieldValue(field.value, '', field.apiName),
        ...(storageField && {
          userId: storageField.userId,
          groupId: storageField.groupId,
        }),
      };
    },
  };
}
