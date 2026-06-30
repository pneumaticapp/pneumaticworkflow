// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { ExtraFieldFile } from '../ExtraFieldFile';
import { EExtraFieldMode, EExtraFieldType, IExtraField } from '../../../../../types/template';
import { TUploadedFile } from '../../../../../utils/uploadFiles';
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
});
