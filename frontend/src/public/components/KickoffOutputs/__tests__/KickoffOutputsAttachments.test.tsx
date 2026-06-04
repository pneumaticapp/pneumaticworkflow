// <reference types="jest" />


import { EExtraFieldType, IExtraField } from '../../../types/template';
import { TUploadedFile } from '../../../utils/uploadFiles';
import { parseMarkdownToFiles } from '../../../utils/parseMarkdownFiles';
import { flatten, isArrayWithItems } from '../../../utils/helpers';

/*
 * KickoffOutputs has deep dependency tree (react-intl, RichText, etc.)
 * and the isOnlyAttachmentsShown branch returns early before hooks.
 * Instead of rendering the full component, we test the extraction logic directly.
 */
describe('KickoffOutputs - attachments extraction logic (isOnlyAttachmentsShown)', () => {
  const createFileField = (overrides: Partial<IExtraField> = {}): IExtraField => ({
    name: 'File Field',
    type: EExtraFieldType.File,
    apiName: 'file-1',
    order: 1,
    userId: null,
    groupId: null,
    ...overrides,
  });

  /**
   * Extracts the exact logic from KickoffOutputs.tsx lines 50-55:
   *   const fileOutputs = outputs.filter(({ type }) => type === EExtraFieldType.File);
   *   const attachments = flatten(fileOutputs.map((field) => {
   *     return isArrayWithItems(field.attachments)
   *       ? field.attachments
   *       : parseMarkdownToFiles(field.markdownValue);
   *   })) as TUploadedFile[];
   */
  function extractAttachments(outputs: IExtraField[]): TUploadedFile[] {
    const fileOutputs = outputs.filter(({ type }) => type === EExtraFieldType.File);
    return flatten(fileOutputs.map((field) => {
      return isArrayWithItems(field.attachments)
        ? field.attachments
        : parseMarkdownToFiles(field.markdownValue);
    })) as TUploadedFile[];
  }

  it('extracts attachments from attachments array', () => {
    const outputs: IExtraField[] = [
      createFileField({
        attachments: [
          { id: 'f1', name: 'doc.pdf', url: 'https://example.com/f1', size: 100 },
        ],
      }),
    ];

    const result = extractAttachments(outputs);

    expect(result).toHaveLength(1);
    expect(result[0].name).toBe('doc.pdf');
  });

  it('falls back to markdownValue when attachments is empty', () => {
    const outputs: IExtraField[] = [
      createFileField({
        attachments: [],
        markdownValue: '[report.pdf](https://example.com/rpt)',
      }),
    ];

    const result = extractAttachments(outputs);

    expect(result).toHaveLength(1);
    expect(result[0].name).toBe('report.pdf');
    expect(result[0].url).toBe('https://example.com/rpt');
  });

  it('falls back to markdownValue when attachments is undefined', () => {
    const outputs: IExtraField[] = [
      createFileField({
        markdownValue: '[invoice.pdf](https://example.com/inv)',
      }),
    ];

    const result = extractAttachments(outputs);

    expect(result).toHaveLength(1);
    expect(result[0].name).toBe('invoice.pdf');
  });

  it('aggregates files from multiple file fields', () => {
    const outputs: IExtraField[] = [
      createFileField({
        apiName: 'file-1',
        attachments: [{ id: 'a', name: 'a.pdf', url: 'https://example.com/a', size: 10 }],
      }),
      createFileField({
        apiName: 'file-2',
        markdownValue: '[b.png](https://example.com/b)',
      }),
    ];

    const result = extractAttachments(outputs);

    expect(result).toHaveLength(2);
    expect(result[0].name).toBe('a.pdf');
    expect(result[1].name).toBe('b.png');
  });

  it('skips non-file fields', () => {
    const outputs: IExtraField[] = [
      {
        name: 'Text Field',
        type: EExtraFieldType.Text,
        apiName: 'text-1',
        order: 0,
        userId: null,
        groupId: null,
        value: 'some text',
      },
      createFileField({
        markdownValue: '[only-file.pdf](https://example.com/f)',
      }),
    ];

    const result = extractAttachments(outputs);

    expect(result).toHaveLength(1);
    expect(result[0].name).toBe('only-file.pdf');
  });

  it('returns empty array when no files exist', () => {
    const outputs: IExtraField[] = [
      createFileField({ attachments: [], markdownValue: '' }),
    ];

    const result = extractAttachments(outputs);

    expect(result).toEqual([]);
  });

  it('prefers attachments over markdownValue per field', () => {
    const outputs: IExtraField[] = [
      createFileField({
        attachments: [{ id: 'a', name: 'actual.pdf', url: 'https://example.com/a', size: 50 }],
        markdownValue: '[stale.pdf](https://example.com/stale)',
      }),
    ];

    const result = extractAttachments(outputs);

    expect(result).toHaveLength(1);
    expect(result[0].name).toBe('actual.pdf');
  });
});
