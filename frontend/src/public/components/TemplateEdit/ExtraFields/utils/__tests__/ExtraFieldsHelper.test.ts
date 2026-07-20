import { ExtraFieldsHelper } from '../ExtraFieldsHelper';
import { EExtraFieldType, IExtraField } from '../../../../../types/template';
import { TUploadedFile } from '../../../../../utils/uploadFiles';

jest.mock('../../../../../utils/getConfig', () => ({
  getBrowserConfigEnv: () => ({
    api: { fileServiceUrl: 'https://files.example.com' },
  }),
}));

const createFileField = (overrides: Partial<IExtraField> = {}): IExtraField => ({
  apiName: 'field-abc123',
  name: 'File Field',
  type: EExtraFieldType.File,
  order: 1,
  userId: null,
  groupId: null,
  ...overrides,
});

describe('ExtraFieldsHelper', () => {
  describe('getFieldsWithValues — File type (markdown_value parsing)', () => {
    it('parses markdownValue into attachments when no storageOutput', () => {
      const field = createFileField({
        markdownValue: '[doc.pdf](https://files.example.com/abc-123)',
      });

      const helper = new ExtraFieldsHelper([field]);
      const result = helper.getFieldsWithValues();

      expect(result).toHaveLength(1);
      expect(result[0].attachments).toEqual([
        {
          id: 'abc-123',
          name: 'doc.pdf',
          url: 'https://files.example.com/abc-123',
          size: 0,
        },
      ]);
    });

    it('generates value as markdown links from parsed attachments', () => {
      const field = createFileField({
        markdownValue: '[doc.pdf](https://files.example.com/abc-123)',
      });

      const helper = new ExtraFieldsHelper([field]);
      const result = helper.getFieldsWithValues();

      expect(result[0].value).toEqual([
        '[doc.pdf](https://files.example.com/abc-123)',
      ]);
    });

    it('parses multiple files from markdownValue', () => {
      const field = createFileField({
        markdownValue:
          '[a.pdf](https://files.example.com/1), [b.png](https://files.example.com/2)',
      });

      const helper = new ExtraFieldsHelper([field]);
      const result = helper.getFieldsWithValues();

      expect(result[0].attachments).toHaveLength(2);
      expect(result[0].attachments![0].name).toBe('a.pdf');
      expect(result[0].attachments![1].name).toBe('b.png');
    });

    it('returns empty attachments and value when markdownValue is empty', () => {
      const field = createFileField({
        markdownValue: '',
      });

      const helper = new ExtraFieldsHelper([field]);
      const result = helper.getFieldsWithValues();

      expect(result[0].attachments).toEqual([]);
      expect(result[0].value).toEqual([]);
    });

    it('returns empty attachments when markdownValue is undefined', () => {
      const field = createFileField();

      const helper = new ExtraFieldsHelper([field]);
      const result = helper.getFieldsWithValues();

      expect(result[0].attachments).toEqual([]);
      expect(result[0].value).toEqual([]);
    });

    it('restores storage attachments over a prefilled server value', () => {
      const serverField = createFileField({
        markdownValue: '[old.pdf](https://files.example.com/old)',
      });

      const storageAttachments: TUploadedFile[] = [
        {
          id: 'new-id',
          name: 'new.pdf',
          url: 'https://files.example.com/new',
          size: 500,
        },
      ];

      const storageField = createFileField({
        attachments: storageAttachments,
      });

      const helper = new ExtraFieldsHelper([serverField], [storageField]);
      const result = helper.getFieldsWithValues();

      expect(result[0].attachments).toEqual(storageAttachments);
    });

    it('uses storageOutput attachments when server field has no value', () => {
      const serverField = createFileField({
        markdownValue: '',
      });

      const storageAttachments: TUploadedFile[] = [
        {
          id: 'new-id',
          name: 'new.pdf',
          url: 'https://files.example.com/new',
          size: 500,
        },
      ];

      const storageField = createFileField({
        attachments: storageAttachments,
      });

      const helper = new ExtraFieldsHelper([serverField], [storageField]);
      const result = helper.getFieldsWithValues();

      expect(result[0].attachments).toEqual(storageAttachments);
      expect(result[0].value).toEqual([
        '[new.pdf](https://files.example.com/new)',
      ]);
    });

    it('filters out isRemoved files from storageOutput', () => {
      const serverField = createFileField({
        markdownValue: '',
      });

      const storageField = createFileField({
        attachments: [
          {
            id: '1',
            name: 'kept.pdf',
            url: 'https://files.example.com/1',
            size: 100,
          },
          {
            id: '2',
            name: 'removed.pdf',
            url: 'https://files.example.com/2',
            size: 200,
            isRemoved: true,
          },
        ],
      });

      const helper = new ExtraFieldsHelper([serverField], [storageField]);
      const result = helper.getFieldsWithValues();

      expect(result[0].attachments).toHaveLength(1);
      expect(result[0].attachments![0].name).toBe('kept.pdf');
    });

    it('uses server attachments when markdownValue is absent', () => {
      const serverField = createFileField({
        markdownValue: undefined,
        attachments: [
          {
            id: 'server-att',
            name: 'server.pdf',
            url: 'https://files.example.com/server',
            size: 100,
          },
        ],
      });

      const helper = new ExtraFieldsHelper([serverField]);
      const result = helper.getFieldsWithValues();

      expect(result[0].attachments).toEqual([
        {
          id: 'server-att',
          name: 'server.pdf',
          url: 'https://files.example.com/server',
          size: 100,
        },
      ]);
      expect(result[0].value).toEqual([
        '[server.pdf](https://files.example.com/server)',
      ]);
    });

    it('falls back to markdownValue when storageOutput has no matching field', () => {
      const serverField = createFileField({
        apiName: 'field-server',
        markdownValue: '[server-file.pdf](https://files.example.com/srv)',
      });

      const storageField = createFileField({
        apiName: 'field-other',
        attachments: [
          {
            id: 'x',
            name: 'other.pdf',
            url: 'https://files.example.com/x',
            size: 0,
          },
        ],
      });

      const helper = new ExtraFieldsHelper([serverField], [storageField]);
      const result = helper.getFieldsWithValues();

      expect(result[0].attachments![0].name).toBe('server-file.pdf');
    });
  });

  describe('getFieldsWithValues — non-File types (sanity checks)', () => {
    it('processes text field with default value', () => {
      const field: IExtraField = {
        apiName: 'field-text',
        name: 'Text Field',
        type: EExtraFieldType.Text,
        order: 1,
        userId: null,
        groupId: null,
        value: 'hello',
      };

      const helper = new ExtraFieldsHelper([field]);
      const result = helper.getFieldsWithValues();

      expect(result[0].value).toBe('hello');
    });

    it('restores a stored number over a prefilled server value', () => {
      const serverField: IExtraField = {
        apiName: 'field-number',
        name: 'Number Field',
        type: EExtraFieldType.Number,
        order: 1,
        userId: null,
        groupId: null,
        value: 0,
      };
      const storageField = { ...serverField, value: 10 };

      const helper = new ExtraFieldsHelper([serverField], [storageField]);
      const result = helper.getFieldsWithValues();

      expect(result[0].value).toBe(10);
    });

    it('returns null for radio field with no selections', () => {
      const field: IExtraField = {
        apiName: 'field-radio',
        name: 'Radio Field',
        type: EExtraFieldType.Radio,
        order: 1,
        userId: null,
        groupId: null,
        selections: [],
      };

      const helper = new ExtraFieldsHelper([field]);
      const result = helper.getFieldsWithValues();

      expect(result).toHaveLength(0);
    });

    it('normalizes an empty radio value to null', () => {
      const field: IExtraField = {
        apiName: 'field-radio',
        name: 'Radio Field',
        type: EExtraFieldType.Radio,
        order: 1,
        userId: null,
        groupId: null,
        selections: ['first', 'second'],
        value: '',
      };

      const helper = new ExtraFieldsHelper([field]);
      const result = helper.getFieldsWithValues();

      expect(result[0].value).toBeNull();
    });

    it('normalizes an empty stored radio value to null', () => {
      const field: IExtraField = {
        apiName: 'field-radio',
        name: 'Radio Field',
        type: EExtraFieldType.Radio,
        order: 1,
        userId: null,
        groupId: null,
        selections: ['first', 'second'],
        value: '',
      };

      const helper = new ExtraFieldsHelper([field], [{ ...field }]);
      const result = helper.getFieldsWithValues();

      expect(result[0].value).toBeNull();
    });
  });

  describe('normalizeFieldsValues', () => {
    it('passes file field value as-is (already markdown array)', () => {
      const field = createFileField({
        value: ['[doc.pdf](https://files.example.com/abc)'],
      });

      const helper = new ExtraFieldsHelper([field]);
      const result = helper.normalizeFieldsValues();

      expect(result).toEqual([
        { 'field-abc123': ['[doc.pdf](https://files.example.com/abc)'] },
      ]);
    });
  });
});
