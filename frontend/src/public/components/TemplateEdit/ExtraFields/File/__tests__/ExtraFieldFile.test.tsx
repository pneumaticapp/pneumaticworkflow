// <reference types="jest" />
import * as React from 'react';
import { act, fireEvent, render, screen } from '@testing-library/react';

import { ExtraFieldFile } from '../ExtraFieldFile';
import { EExtraFieldMode, EExtraFieldType, IExtraField } from '../../../../../types/template';
import { TUploadedFile, uploadFiles } from '../../../../../utils/uploadFiles';
import { intlMock } from '../../../../../__stubs__/intlMock';

jest.mock('../../../../../utils/uploadFiles', () => ({
  uploadFiles: jest.fn(),
  MAX_FILE_SIZE: 100 * 1024 * 1024,
}));

jest.mock('../../../../../utils/getConfig', () => ({
  getBrowserConfigEnv: () => ({
    api: { fileServiceUrl: 'https://files.example.com' },
  }),
}));

jest.mock('../../../../../utils/logger', () => ({
  logger: { error: jest.fn(), info: jest.fn(), warn: jest.fn() },
}));

jest.mock('../../../../UI/Notifications', () => ({
  NotificationManager: { warning: jest.fn(), notifyApiError: jest.fn() },
}));

describe('ExtraFieldFile', () => {
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

  const editFieldMock = jest.fn();

  const baseProps = {
    field: createFileField(),
    intl: intlMock,
    mode: EExtraFieldMode.ProcessRun,
    editField: editFieldMock,
    accountId: 1,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('initial file loading', () => {
    it('renders with attachments from field.attachments', () => {
      const attachments: TUploadedFile[] = [
        { id: 'att-1', name: 'report.pdf', url: 'https://files.example.com/att-1', size: 1024 },
      ];

      render(
        React.createElement(ExtraFieldFile as React.FC<any>, {
          ...baseProps,
          field: createFileField({ attachments }),
        }),
      );

      expect(screen.getByText('report.pdf')).toBeInTheDocument();
    });

    it('parses markdownValue when attachments is empty', () => {
      render(
        React.createElement(ExtraFieldFile as React.FC<any>, {
          ...baseProps,
          field: createFileField({
            attachments: [],
            markdownValue: '[contract.pdf](https://files.example.com/abc)',
          }),
        }),
      );

      expect(screen.getByText('contract.pdf')).toBeInTheDocument();
    });

    it('parses markdownValue when attachments is undefined', () => {
      render(
        React.createElement(ExtraFieldFile as React.FC<any>, {
          ...baseProps,
          field: createFileField({
            markdownValue: '[invoice.pdf](https://files.example.com/inv)',
          }),
        }),
      );

      expect(screen.getByText('invoice.pdf')).toBeInTheDocument();
    });

    it('renders multiple files from markdownValue', () => {
      render(
        React.createElement(ExtraFieldFile as React.FC<any>, {
          ...baseProps,
          field: createFileField({
            markdownValue: '[a.pdf](https://files.example.com/1), [b.docx](https://files.example.com/2)',
          }),
        }),
      );

      expect(screen.getByText('a.pdf')).toBeInTheDocument();
      expect(screen.getByText('b.docx')).toBeInTheDocument();
    });

    it('prefers attachments over markdownValue', () => {
      const attachments: TUploadedFile[] = [
        { id: 'real', name: 'real.pdf', url: 'https://files.example.com/real', size: 500 },
      ];

      render(
        React.createElement(ExtraFieldFile as React.FC<any>, {
          ...baseProps,
          field: createFileField({
            attachments,
            markdownValue: '[old.pdf](https://files.example.com/old)',
          }),
        }),
      );

      expect(screen.getByText('real.pdf')).toBeInTheDocument();
      expect(screen.queryByText('old.pdf')).not.toBeInTheDocument();
    });

    it('syncs displayed files when field attachments change', () => {
      const attachments: TUploadedFile[] = [
        { id: 'att-1', name: 'report.pdf', url: 'https://files.example.com/att-1', size: 1024 },
      ];

      const { rerender } = render(
        React.createElement(ExtraFieldFile as React.FC<any>, {
          ...baseProps,
          field: createFileField({ attachments }),
        }),
      );

      expect(screen.getByText('report.pdf')).toBeInTheDocument();

      const updatedAttachments: TUploadedFile[] = [
        { id: 'att-2', name: 'updated.pdf', url: 'https://files.example.com/att-2', size: 2048 },
      ];

      rerender(
        React.createElement(ExtraFieldFile as React.FC<any>, {
          ...baseProps,
          field: createFileField({ attachments: updatedAttachments }),
        }),
      );

      expect(screen.queryByText('report.pdf')).not.toBeInTheDocument();
      expect(screen.getByText('updated.pdf')).toBeInTheDocument();
    });

    it('renders nothing when no attachments and no markdownValue', () => {
      const { container } = render(
        React.createElement(ExtraFieldFile as React.FC<any>, {
          ...baseProps,
          field: createFileField(),
        }),
      );

      // No files grid should appear
      expect(container.querySelector('[class*="files-grid"]')).toBeNull();
    });
  });

  describe('kickoff mode rendering', () => {
    it('renders upload button placeholder in kickoff mode', () => {
      render(
        React.createElement(ExtraFieldFile as React.FC<any>, {
          ...baseProps,
          mode: EExtraFieldMode.Kickoff,
          field: createFileField(),
        }),
      );

      expect(screen.getByDisplayValue('Attachments')).toBeInTheDocument();
    });
  });

  describe('upload handling', () => {
    it('merges uploaded files against current state when field attachments change during upload', async () => {
      let resolveUpload: (files: TUploadedFile[]) => void = () => undefined;

      (uploadFiles as jest.Mock).mockImplementation(
        () =>
          new Promise<TUploadedFile[]>((resolve) => {
            resolveUpload = resolve;
          }),
      );

      const attachments: TUploadedFile[] = [
        { id: 'att-1', name: 'existing.pdf', url: 'https://files.example.com/att-1', size: 1024 },
      ];

      const { container, rerender } = render(
        React.createElement(ExtraFieldFile as React.FC<any>, {
          ...baseProps,
          field: createFileField({ attachments }),
        }),
      );

      const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
      const file = new File(['content'], 'uploaded.pdf', { type: 'application/pdf' });

      fireEvent.change(fileInput, { target: { files: [file] } });

      const updatedAttachments: TUploadedFile[] = [
        { id: 'att-2', name: 'server.pdf', url: 'https://files.example.com/att-2', size: 2048 },
      ];

      rerender(
        React.createElement(ExtraFieldFile as React.FC<any>, {
          ...baseProps,
          field: createFileField({ attachments: updatedAttachments }),
        }),
      );

      await act(async () => {
        resolveUpload([
          { id: 'new-1', name: 'uploaded.pdf', url: 'https://files.example.com/new-1', size: 100 },
        ]);
      });

      expect(editFieldMock).toHaveBeenCalledWith({
        value: [
          '[server.pdf](https://files.example.com/att-2)',
          '[uploaded.pdf](https://files.example.com/new-1)',
        ],
        attachments: [
          updatedAttachments[0],
          { id: 'new-1', name: 'uploaded.pdf', url: 'https://files.example.com/new-1', size: 100 },
        ],
      });
    });

    it('ignores an upload that resolves after the field unmounts', async () => {
      let resolveUpload: (files: TUploadedFile[]) => void = () => undefined;
      const onUploadStateChange = jest.fn();
      (uploadFiles as jest.Mock).mockImplementation(
        () => new Promise<TUploadedFile[]>((resolve) => {
          resolveUpload = resolve;
        }),
      );
      const { container, unmount } = render(
        React.createElement(ExtraFieldFile as React.FC<any>, {
          ...baseProps,
          onUploadStateChange,
        }),
      );
      const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;

      fireEvent.change(fileInput, {
        target: { files: [new File(['content'], 'uploaded.pdf', { type: 'application/pdf' })] },
      });
      unmount();

      await act(async () => {
        resolveUpload([
          { id: 'new-1', name: 'uploaded.pdf', url: 'https://files.example.com/new-1', size: 100 },
        ]);
      });

      expect(editFieldMock).not.toHaveBeenCalled();
      expect(onUploadStateChange).toHaveBeenNthCalledWith(1, true);
      expect(onUploadStateChange).toHaveBeenNthCalledWith(2, false);
    });

    it('keeps an upload active when the notification callback changes', async () => {
      let resolveUpload: (files: TUploadedFile[]) => void = () => undefined;
      const firstUploadStateChange = jest.fn();
      const nextUploadStateChange = jest.fn();
      (uploadFiles as jest.Mock).mockImplementation(
        () => new Promise<TUploadedFile[]>((resolve) => {
          resolveUpload = resolve;
        }),
      );
      const { container, rerender } = render(
        React.createElement(ExtraFieldFile as React.FC<any>, {
          ...baseProps,
          onUploadStateChange: firstUploadStateChange,
        }),
      );
      const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;

      fireEvent.change(fileInput, {
        target: { files: [new File(['content'], 'uploaded.pdf', { type: 'application/pdf' })] },
      });
      rerender(
        React.createElement(ExtraFieldFile as React.FC<any>, {
          ...baseProps,
          onUploadStateChange: nextUploadStateChange,
        }),
      );

      await act(async () => {
        resolveUpload([
          { id: 'new-1', name: 'uploaded.pdf', url: 'https://files.example.com/new-1', size: 100 },
        ]);
      });

      expect(editFieldMock).toHaveBeenCalledWith(expect.objectContaining({
        attachments: [expect.objectContaining({ id: 'new-1' })],
      }));
      expect(firstUploadStateChange).toHaveBeenCalledWith(true);
      expect(nextUploadStateChange).toHaveBeenCalledWith(false);
    });
  });
});
