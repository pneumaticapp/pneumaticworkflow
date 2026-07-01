// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { FileOutput } from '../FileOutput';
import { EExtraFieldType } from '../../../types/template';
import { TUploadedFile } from '../../../utils/uploadFiles';
import { intlMock } from '../../../__stubs__/intlMock';

jest.mock('../../Attachments', () => {
  const React = require('react');
  return {
    Attachments: ({ attachments }: { attachments: any[] }) =>
      React.createElement(
        'div',
        { 'data-testid': 'attachments' },
        attachments.map((a: any) =>
          React.createElement('span', { key: a.id, 'data-testid': `attachment-${a.id}` }, a.name),
        ),
      ),
  };
});

jest.mock('../../../utils/getConfig', () => ({
  getBrowserConfigEnv: () => ({
    api: { fileServiceUrl: 'https://files.example.com' },
  }),
}));

describe('FileOutput', () => {
  const formatMsg = (id: string) => intlMock.formatMessage({ id });
  const UNFILLED = formatMsg('template.kick-off-form-unfilled-value');

  const baseProps = {
    name: 'Documents',
    type: EExtraFieldType.File,
    apiName: 'file-field',
    order: 1,
    userId: null,
    groupId: null,
  };

  it('renders attachments from attachments array when present', () => {
    const attachments: TUploadedFile[] = [
      { id: 'att-1', name: 'report.pdf', url: 'https://files.example.com/att-1', size: 1024 },
    ];

    render(React.createElement(FileOutput, { ...baseProps, attachments }));

    expect(screen.getByTestId('attachments')).toBeInTheDocument();
    expect(screen.getByText('report.pdf')).toBeInTheDocument();
  });

  it('parses markdownValue when attachments array is empty', () => {
    render(
      React.createElement(FileOutput, {
        ...baseProps,
        attachments: [],
        markdownValue: '[contract.pdf](https://files.example.com/abc-123)',
      }),
    );

    expect(screen.getByTestId('attachments')).toBeInTheDocument();
    expect(screen.getByText('contract.pdf')).toBeInTheDocument();
  });

  it('parses markdownValue when attachments is undefined', () => {
    render(
      React.createElement(FileOutput, {
        ...baseProps,
        markdownValue: '[invoice.pdf](https://files.example.com/inv-1)',
      }),
    );

    expect(screen.getByText('invoice.pdf')).toBeInTheDocument();
  });

  it('renders multiple files from markdownValue', () => {
    const markdownValue =
      '[a.pdf](https://files.example.com/1), [b.png](https://files.example.com/2)';

    render(React.createElement(FileOutput, { ...baseProps, markdownValue }));

    expect(screen.getByText('a.pdf')).toBeInTheDocument();
    expect(screen.getByText('b.png')).toBeInTheDocument();
  });

  it('prefers attachments array over markdownValue', () => {
    const attachments: TUploadedFile[] = [
      { id: 'real-1', name: 'real.pdf', url: 'https://files.example.com/real-1', size: 500 },
    ];

    render(
      React.createElement(FileOutput, {
        ...baseProps,
        attachments,
        markdownValue: '[stale.pdf](https://files.example.com/stale)',
      }),
    );

    expect(screen.getByText('real.pdf')).toBeInTheDocument();
    expect(screen.queryByText('stale.pdf')).not.toBeInTheDocument();
  });

  it('displays unfilled text when no attachments and no markdownValue', () => {
    render(React.createElement(FileOutput, { ...baseProps }));

    expect(screen.getByText(UNFILLED)).toBeInTheDocument();
  });

  it('displays unfilled text when markdownValue is empty string', () => {
    render(React.createElement(FileOutput, { ...baseProps, markdownValue: '' }));

    expect(screen.getByText(UNFILLED)).toBeInTheDocument();
  });
});
