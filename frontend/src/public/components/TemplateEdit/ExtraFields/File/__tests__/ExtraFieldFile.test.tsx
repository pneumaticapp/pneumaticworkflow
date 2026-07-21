import * as React from 'react';
import { act, fireEvent, render, screen } from '@testing-library/react';

import { ExtraFieldFile } from '../ExtraFieldFile';
import { FieldLabel } from '../../utils/FieldLabel';
import { IWorkflowExtraFieldProps } from '../../types';
import { intlMock } from '../../../../../__stubs__/intlMock';
import { makeExtraField } from '../../../../../__stubs__/fields.factory';
import { EExtraFieldMode, EExtraFieldType, IExtraField } from '../../../../../types/template';
import { EFieldLabelPosition } from '../../../../../types/fieldset';
import { TUploadedFile, uploadFiles } from '../../../../../utils/uploadFiles';

jest.mock('../../utils/FieldLabel', () => ({
  FieldLabel: jest.fn(() => null),
}));

jest.mock('../../../../icons', () => ({
  PencilSmallIcon: () => null,
  RemoveIcon: () => null,
}));

jest.mock('../../../../../utils/validators', () => ({
  validateKickoffFieldName: jest.fn(() => ''),
}));

jest.mock('../../../../../utils/uploadFiles', () => ({
  uploadFiles: jest.fn(),
  MAX_FILE_SIZE: 100 * 1024 * 1024,
}));

jest.mock('../../../../../utils/getConfig', () => ({
  getBrowserConfigEnv: () => ({
    api: { fileServiceUrl: 'https://files.example.com' },
  }),
}));

jest.mock('../../../../IntlMessages', () => ({
  IntlMessages: jest.fn(() => null),
}));

jest.mock('../../../../UI/Notifications', () => ({
  NotificationManager: { warning: jest.fn(), success: jest.fn(), notifyApiError: jest.fn() },
}));

jest.mock('../ExtraFieldFilesGrid', () => ({
  ExtraFieldFilesGrid: jest.fn(({ attachments }: { attachments: TUploadedFile[] }) => {
    if (!attachments?.length) {
      return null;
    }

    return (
      <>
        {attachments
          .filter((file) => !file.isRemoved)
          .map((file) => (
            <span key={file.id}>{file.name}</span>
          ))}
      </>
    );
  }),
}));

jest.mock('../../../../UI/Buttons/Button', () => ({
  Button: jest.fn(() => null),
}));

jest.mock('../../../../../utils/logger', () => ({
  logger: { error: jest.fn(), info: jest.fn(), warn: jest.fn() },
}));

describe('ExtraFieldFile', () => {
  const mockEditField = jest.fn();

  const baseProps: IWorkflowExtraFieldProps = {
    field: makeExtraField({ name: 'Attachment', type: EExtraFieldType.File }),
    intl: intlMock,
    editField: mockEditField,
    mode: EExtraFieldMode.Kickoff,
    isDisabled: false,
    accountId: 1,
    labelPosition: EFieldLabelPosition.Top,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('label-left support', () => {
    it('Kickoff + labelPosition=Left: renders FieldLabel', () => {
      render(<ExtraFieldFile {...baseProps} labelPosition={EFieldLabelPosition.Left} />);

      const fieldLabelMock = FieldLabel as jest.Mock;
      expect(fieldLabelMock).toHaveBeenCalled();
    });

    it('Kickoff + labelPosition=Top: no FieldLabel', () => {
      render(<ExtraFieldFile {...baseProps} labelPosition={EFieldLabelPosition.Top} />);

      const fieldLabelMock = FieldLabel as jest.Mock;
      expect(fieldLabelMock).not.toHaveBeenCalled();
    });

    it('ProcessRun + labelPosition=Left: renders FieldLabel with aligned-start class', () => {
      render(
        <ExtraFieldFile
          {...baseProps}
          mode={EExtraFieldMode.ProcessRun}
          labelPosition={EFieldLabelPosition.Left}
        />,
      );

      const fieldLabelMock = FieldLabel as jest.Mock;
      expect(fieldLabelMock).toHaveBeenCalled();
      expect(fieldLabelMock).toHaveBeenCalledWith(
        expect.objectContaining({
          className: expect.stringContaining('aligned-start'),
        }),
        {},
      );
    });

    it('ProcessRun + labelPosition=Top: renders static name div, no FieldLabel', () => {
      render(
        <ExtraFieldFile
          {...baseProps}
          mode={EExtraFieldMode.ProcessRun}
          labelPosition={EFieldLabelPosition.Top}
        />,
      );

      const fieldLabelMock = FieldLabel as jest.Mock;
      expect(fieldLabelMock).not.toHaveBeenCalled();
      expect(screen.getByText('Attachment')).toBeInTheDocument();
    });
  });

  describe('initial file loading', () => {
    const createFileField = (overrides: Partial<IExtraField> = {}): IExtraField => ({
      apiName: 'file-abc',
      name: 'Attachments',
      type: EExtraFieldType.File,
      order: 1,
      isRequired: false,
      userId: null,
      groupId: null,
      ...overrides,
    });

    const processRunProps = {
      ...baseProps,
      mode: EExtraFieldMode.ProcessRun,
    };

    it('renders with attachments from field.attachments', () => {
      const attachments: TUploadedFile[] = [
        { id: 'att-1', name: 'report.pdf', url: 'https://files.example.com/att-1', size: 1024 },
      ];

      render(<ExtraFieldFile {...processRunProps} field={createFileField({ attachments })} />);

      expect(screen.getByText('report.pdf')).toBeInTheDocument();
    });

    it('parses markdownValue when attachments is empty', () => {
      render(
        <ExtraFieldFile
          {...processRunProps}
          field={createFileField({
            attachments: [],
            markdownValue: '[contract.pdf](https://files.example.com/abc)',
          })}
        />,
      );

      expect(screen.getByText('contract.pdf')).toBeInTheDocument();
    });

    it('parses markdownValue when attachments is undefined', () => {
      render(
        <ExtraFieldFile
          {...processRunProps}
          field={createFileField({
            attachments: undefined,
            markdownValue: '[invoice.pdf](https://files.example.com/inv)',
          })}
        />,
      );

      expect(screen.getByText('invoice.pdf')).toBeInTheDocument();
    });

    it('renders multiple files from markdownValue', () => {
      render(
        <ExtraFieldFile
          {...processRunProps}
          field={createFileField({
            markdownValue: '[a.pdf](https://files.example.com/1), [b.docx](https://files.example.com/2)',
          })}
        />,
      );

      expect(screen.getByText('a.pdf')).toBeInTheDocument();
      expect(screen.getByText('b.docx')).toBeInTheDocument();
    });

    it('prefers attachments over markdownValue', () => {
      const attachments: TUploadedFile[] = [
        { id: 'real', name: 'real.pdf', url: 'https://files.example.com/real', size: 500 },
      ];

      render(
        <ExtraFieldFile
          {...processRunProps}
          field={createFileField({
            attachments,
            markdownValue: '[old.pdf](https://files.example.com/old)',
          })}
        />,
      );

      expect(screen.getByText('real.pdf')).toBeInTheDocument();
      expect(screen.queryByText('old.pdf')).not.toBeInTheDocument();
    });

    it('renders nothing when no attachments and no markdownValue', () => {
      const { container } = render(<ExtraFieldFile {...processRunProps} field={createFileField()} />);

      expect(container.querySelector('[class*="files-grid"]')).toBeNull();
    });

    it('updates displayed files when field attachments change', () => {
      const { rerender } = render(
        <ExtraFieldFile {...processRunProps} field={createFileField({ attachments: [] })} />,
      );

      rerender(
        <ExtraFieldFile
          {...processRunProps}
          field={createFileField({
            attachments: [
              { id: 'new', name: 'updated.pdf', url: 'https://files.example.com/updated', size: 100 },
            ],
          })}
        />,
      );

      expect(screen.getByText('updated.pdf')).toBeInTheDocument();
    });

    it('appends an in-flight upload to attachments received from a parent sync', async () => {
      let resolveUpload: (files: TUploadedFile[]) => void = () => undefined;
      (uploadFiles as jest.Mock).mockReturnValue(new Promise<TUploadedFile[]>((resolve) => {
        resolveUpload = resolve;
      }));
      const oldAttachment = {
        id: 'old',
        name: 'old.pdf',
        url: 'https://files.example.com/old',
        size: 100,
      };
      const syncedAttachment = {
        id: 'synced',
        name: 'synced.pdf',
        url: 'https://files.example.com/synced',
        size: 100,
      };
      const uploadedAttachment = {
        id: 'uploaded',
        name: 'uploaded.pdf',
        url: 'https://files.example.com/uploaded',
        size: 100,
      };
      const { container, rerender } = render(
        <ExtraFieldFile
          {...processRunProps}
          field={createFileField({ attachments: [oldAttachment] })}
        />,
      );

      fireEvent.change(container.querySelector('input[type="file"]')!, {
        target: { files: [new File(['content'], 'uploaded.pdf')] },
      });
      rerender(
        <ExtraFieldFile
          {...processRunProps}
          field={createFileField({ attachments: [syncedAttachment] })}
        />,
      );
      await act(async () => {
        resolveUpload([uploadedAttachment]);
        await Promise.resolve();
      });

      expect(mockEditField).toHaveBeenLastCalledWith(expect.objectContaining({
        attachments: [syncedAttachment, uploadedAttachment],
      }));
    });
  });

  describe('kickoff mode rendering', () => {
    it('renders upload button placeholder in kickoff mode', () => {
      render(
        <ExtraFieldFile
          {...baseProps}
          mode={EExtraFieldMode.Kickoff}
          field={makeExtraField({ name: 'Attachments', type: EExtraFieldType.File })}
        />,
      );

      expect(screen.getByDisplayValue('Attachments')).toBeInTheDocument();
    });
  });
});
