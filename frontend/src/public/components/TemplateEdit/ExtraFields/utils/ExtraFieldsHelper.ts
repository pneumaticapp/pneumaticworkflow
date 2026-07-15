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

  private static hasServerValue(field: IExtraField): boolean {
    if (field.type === EExtraFieldType.File) {
      return Boolean(field.markdownValue) || Boolean(field.attachments?.length);
    }

    if (field.type === EExtraFieldType.User) {
      return Boolean(field.userId || field.groupId);
    }

    if (field.type === EExtraFieldType.Checkbox) {
      return Array.isArray(field.value) && field.value.length > 0;
    }

    if (field.type === EExtraFieldType.Number) {
      return field.value !== null && field.value !== undefined && field.value !== '';
    }

    return Boolean(field.value);
  }

  private getFieldValue = (
    initialValue: TExtraFieldValue | undefined,
    defaultValue: TExtraFieldValue,
    fieldApiName: string,
    field: IExtraField,
  ) => {
    const normalizedInitialValue = initialValue === '' || (Array.isArray(initialValue) && initialValue.length === 0)
      ? null
      : initialValue;
    const storageValue = this.getStorageField(fieldApiName)?.value;
    const normalizedStorageValue = storageValue === '' || (Array.isArray(storageValue) && storageValue.length === 0)
      ? null
      : storageValue;

    if (ExtraFieldsHelper.hasServerValue(field)) {
      return normalizedInitialValue ?? defaultValue;
    }

    return normalizedStorageValue ?? normalizedInitialValue ?? defaultValue;
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
      const serverAttachmentsFromMarkdown = parseMarkdownToFiles(field.markdownValue);
      const serverAttachmentsFromField = field.attachments?.filter(({ isRemoved }) => !isRemoved) ?? [];
      let initialAttachments: IExtraField['attachments'] | null = null;

      if (serverAttachmentsFromMarkdown.length > 0) {
        initialAttachments = serverAttachmentsFromMarkdown;
      } else if (serverAttachmentsFromField.length > 0) {
        initialAttachments = serverAttachmentsFromField;
      }
      const storageAttachments = this.getStorageField(field.apiName)?.attachments?.filter(
        ({ isRemoved }) => !isRemoved,
      );
      const attachments = ExtraFieldsHelper.hasServerValue(field)
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
