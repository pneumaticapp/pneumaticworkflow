import React from 'react';
import { render, screen } from '@testing-library/react';

import { KickoffOutputs, EKickoffOutputsViewModes } from '../KickoffOutputs';
import { makeExtraField } from '../../../__stubs__/fields.factory';
import { makeFieldsetRuntime } from '../../../__stubs__/fieldsets.factory';
import { intlMock } from '../../../__stubs__/intlMock';
import { EExtraFieldType, IExtraField } from '../../../types/template';
import { Attachments } from '../../Attachments';

type TOutputMockProps = Pick<IExtraField, 'apiName' | 'name'>;

jest.mock('../../Attachments', () => ({
  Attachments: jest.fn(() => null),
}));

jest.mock('../../../utils/getConfig', () => ({
  getBrowserConfigEnv: () => ({
    api: { fileServiceUrl: 'https://files.example.com' },
  }),
}));

jest.mock('../CheckboxOutput', () => ({ CheckboxOutput: () => null }));
jest.mock('../RadioOutput', () => ({ RadioOutput: () => null }));
jest.mock('../TextOutput', () => ({
  TextOutput: jest.fn(({ apiName, name }: TOutputMockProps) => (
    <div data-testid={`text-output-${apiName}`}>{name}</div>
  )),
}));
jest.mock('../UrlOutput', () => ({ UrlOutput: () => null }));
jest.mock('../FileOutput', () => ({
  FileOutput: jest.fn(({ apiName, name }: TOutputMockProps) => (
    <div data-testid={`file-output-${apiName}`}>{name}</div>
  )),
}));
jest.mock('../UserOutput', () => ({ UserOutput: () => null }));
jest.mock('../../icons', () => ({ EditIcon: () => null }));
jest.mock('../../RichText', () => ({ RichText: () => null }));

describe('KickoffOutputs', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const getAttachmentsProps = () => {
    const mock = Attachments as jest.Mock;
    const lastCall = mock.mock.calls[mock.mock.calls.length - 1];
    return lastCall[0].attachments;
  };

  const baseProps = {
    viewMode: EKickoffOutputsViewModes.Short,
    isOnlyAttachmentsShown: true,
  };

  it('does not render the block when there are neither plain fields nor fieldsets', () => {
    const { container } = render(
      React.createElement(KickoffOutputs, {
        viewMode: EKickoffOutputsViewModes.Detailed,
        outputs: [],
        fieldsets: [],
      }),
    );

    expect(container).toBeEmptyDOMElement();
  });

  it('interleaves plain fields and fieldsets in a single list ordered by `order` descending', () => {
    const fieldA = makeExtraField({ apiName: 'fa', order: 1, value: 'av' });
    const fieldB = makeExtraField({ apiName: 'fb', order: 4, value: 'bv' });
    const fsM = makeFieldsetRuntime({
      apiNameBinding: 'fs-m',
      order: 3,
      fields: [makeExtraField({ apiName: 'fs-m-1', value: 'mv' })],
    });
    const fsN = makeFieldsetRuntime({
      apiNameBinding: 'fs-n',
      order: 2,
      fields: [makeExtraField({ apiName: 'fs-n-1', value: 'nv' })],
    });

    render(
      React.createElement(KickoffOutputs, {
        viewMode: EKickoffOutputsViewModes.Short,
        outputs: [fieldA, fieldB],
        fieldsets: [fsM, fsN],
      }),
    );

    const rendered = screen.getAllByTestId(/^text-output-/);
    expect(rendered.map((el) => el.getAttribute('data-testid'))).toEqual([
      'text-output-fb',
      'text-output-fs-m-1',
      'text-output-fs-n-1',
      'text-output-fa',
    ]);
  });

  it('in full mode renders fieldset group: title, description and only non-empty fields', () => {
    const fieldset = makeFieldsetRuntime({
      name: 'Tech Catalog Name',
      title: 'User Contacts Title',
      description: 'Reachout details',
      order: 1,
      fields: [
        makeExtraField({ apiName: 'email', name: 'Email', value: 'a@b.com', order: 1 }),
        makeExtraField({ apiName: 'phone', name: 'Phone', order: 2 }),
        makeExtraField({ apiName: 'city', name: 'City', value: 'NY', order: 3 }),
      ],
    });

    render(
      React.createElement(KickoffOutputs, {
        viewMode: EKickoffOutputsViewModes.Short,
        outputs: [],
        fieldsets: [fieldset],
      }),
    );

    expect(screen.getByText('User Contacts Title')).toBeInTheDocument();
    expect(screen.queryByText('Tech Catalog Name')).not.toBeInTheDocument();
    expect(screen.getByText('Reachout details')).toBeInTheDocument();

    expect(screen.getByTestId('text-output-email')).toBeInTheDocument();
    expect(screen.getByTestId('text-output-city')).toBeInTheDocument();
    expect(screen.queryByTestId('text-output-phone')).toBeNull();
  });

  it('renders a file field inside a fieldset that has no value but has attachments', () => {
    const fileField = makeExtraField({
      apiName: 'doc',
      name: 'Document',
      type: EExtraFieldType.File,
      value: null,
      attachments: [{ id: '1', url: 'doc.pdf', name: 'doc.pdf', size: 10 }],
    });

    const fieldset = makeFieldsetRuntime({
      name: 'Docs',
      title: 'Docs',
      fields: [fileField],
    });

    render(
      React.createElement(KickoffOutputs, {
        viewMode: EKickoffOutputsViewModes.Short,
        outputs: [],
        fieldsets: [fieldset],
      }),
    );

    expect(screen.getByTestId('file-output-doc')).toBeInTheDocument();
  });

  it('in truncated mode renders fieldset group title and only the first field', () => {
    const fieldset = makeFieldsetRuntime({
      name: 'Profile',
      title: 'Profile',
      order: 5,
      fields: [
        makeExtraField({ apiName: 'first', name: 'First', value: 'one' }),
        makeExtraField({ apiName: 'second', name: 'Second', value: 'two' }),
        makeExtraField({ apiName: 'third', name: 'Third', value: 'three' }),
      ],
    });

    render(
      React.createElement(KickoffOutputs, {
        viewMode: EKickoffOutputsViewModes.Short,
        outputs: [],
        fieldsets: [fieldset],
        isTruncated: true,
      }),
    );

    expect(screen.getByText('Profile')).toBeInTheDocument();
    expect(screen.getByTestId('text-output-first')).toBeInTheDocument();
    expect(screen.queryByTestId('text-output-second')).toBeNull();
    expect(screen.queryByTestId('text-output-third')).toBeNull();
  });

  it('in truncated mode does not crash on a fieldset with an empty fields list', () => {
    const fieldset = makeFieldsetRuntime({
      name: 'Empty Group',
      order: 1,
    });

    expect(() =>
      render(
        React.createElement(KickoffOutputs, {
          viewMode: EKickoffOutputsViewModes.Short,
          outputs: [],
          fieldsets: [fieldset],
          isTruncated: true,
        }),
      ),
    ).not.toThrow();

    expect(screen.queryByTestId(/^text-output-/)).toBeNull();
    expect(screen.queryByTestId(/^file-output-/)).toBeNull();
  });

  describe('isOnlyAttachmentsShown — collecting attachments from fieldsets', () => {
    it('collects file attachments from both outputs and fieldsets respecting order', () => {
      const attachment1 = { id: '1', url: 'file1.pdf', name: 'file1.pdf', size: 100 };
      const attachment2 = { id: '2', url: 'file2.png', name: 'file2.png', size: 200 };
      const attachment3 = { id: '3', url: 'file3.doc', name: 'file3.doc', size: 300 };

      const fileOutput = makeExtraField({
        type: EExtraFieldType.File,
        order: 2,
        attachments: [attachment1],
      });

      const stringOutput = makeExtraField({
        value: 'some text',
      });

      const fieldset = makeFieldsetRuntime({
        order: 1,
        fields: [
          makeExtraField({ type: EExtraFieldType.File, attachments: [attachment2] }),
          makeExtraField({ value: 'ignored' }),
          makeExtraField({ type: EExtraFieldType.File, attachments: [attachment3] }),
        ],
      });

      render(
        React.createElement(KickoffOutputs, {
          ...baseProps,
          outputs: [stringOutput, fileOutput],
          fieldsets: [fieldset],
        }),
      );

      expect(Attachments as jest.Mock).toHaveBeenCalledTimes(1);

      const attachments = getAttachmentsProps();
      expect(attachments).toEqual([attachment1, attachment2, attachment3]);
    });

    it('falls back to markdownValue for a plain File field when attachments is empty', () => {
      const fileOutput = makeExtraField({
        type: EExtraFieldType.File,
        order: 1,
        attachments: [],
        markdownValue: '[report.pdf](https://files.example.com/rpt-1)',
      });

      render(
        React.createElement(KickoffOutputs, {
          ...baseProps,
          outputs: [fileOutput],
          fieldsets: [],
        }),
      );

      expect(Attachments as jest.Mock).toHaveBeenCalledTimes(1);
      expect(getAttachmentsProps()).toEqual([
        expect.objectContaining({
          id: 'rpt-1',
          name: 'report.pdf',
          url: 'https://files.example.com/rpt-1',
        }),
      ]);
    });

    it('falls back to markdownValue for a File field inside a fieldset when attachments is empty', () => {
      const fieldset = makeFieldsetRuntime({
        order: 1,
        fields: [
          makeExtraField({
            type: EExtraFieldType.File,
            attachments: [],
            markdownValue: '[invoice.pdf](https://files.example.com/inv-1)',
          }),
        ],
      });

      render(
        React.createElement(KickoffOutputs, {
          ...baseProps,
          outputs: [],
          fieldsets: [fieldset],
        }),
      );

      expect(Attachments as jest.Mock).toHaveBeenCalledTimes(1);
      expect(getAttachmentsProps()).toEqual([
        expect.objectContaining({
          id: 'inv-1',
          name: 'invoice.pdf',
          url: 'https://files.example.com/inv-1',
        }),
      ]);
    });

    it('prefers attachments over markdownValue for a plain File field', () => {
      const attachment = {
        id: 'att-1',
        url: 'https://files.example.com/att-1',
        name: 'actual.pdf',
        size: 50,
      };

      const fileOutput = makeExtraField({
        type: EExtraFieldType.File,
        order: 1,
        attachments: [attachment],
        markdownValue: '[stale.pdf](https://files.example.com/stale)',
      });

      render(
        React.createElement(KickoffOutputs, {
          ...baseProps,
          outputs: [fileOutput],
          fieldsets: [],
        }),
      );

      expect(Attachments as jest.Mock).toHaveBeenCalledTimes(1);
      expect(getAttachmentsProps()).toEqual([attachment]);
    });

    it('collects attachments from plain fields and markdown from fieldset File fields together', () => {
      const attachment = {
        id: 'plain-1',
        url: 'https://files.example.com/plain-1',
        name: 'plain.pdf',
        size: 10,
      };

      const fileOutput = makeExtraField({
        type: EExtraFieldType.File,
        order: 2,
        attachments: [attachment],
      });

      const fieldset = makeFieldsetRuntime({
        order: 1,
        fields: [
          makeExtraField({
            type: EExtraFieldType.File,
            attachments: [],
            markdownValue: '[from-fs.pdf](https://files.example.com/from-fs)',
          }),
        ],
      });

      render(
        React.createElement(KickoffOutputs, {
          ...baseProps,
          outputs: [fileOutput],
          fieldsets: [fieldset],
        }),
      );

      expect(Attachments as jest.Mock).toHaveBeenCalledTimes(1);
      expect(getAttachmentsProps()).toEqual([
        attachment,
        expect.objectContaining({
          id: 'from-fs',
          name: 'from-fs.pdf',
          url: 'https://files.example.com/from-fs',
        }),
      ]);
    });
  });

  describe('Hidden fields (isHidden)', () => {
    const formatMsg = (id: string) => intlMock.formatMessage({ id });
    const KICKOFF_TITLE = formatMsg('template.kick-off-form-title');
    const EDIT_KICKOFF_LABEL = formatMsg('kickoff-output.edit.edit-kickoff');

    it('skips hidden fields among plain fields and inside fieldsets', () => {
      const outputs = [
        makeExtraField({ apiName: 'plain-hidden', name: 'Plain Hidden', value: 'stale', isHidden: true, order: 3 }),
        makeExtraField({ apiName: 'plain-visible', name: 'Plain Visible', value: 'ok', isHidden: false, order: 2 }),
        makeExtraField({ apiName: 'plain-undef', name: 'Plain Undef', value: 'ok2', isHidden: undefined, order: 1 }),
      ];
      const fieldset = makeFieldsetRuntime({
        apiNameBinding: 'fs-mixed',
        title: 'Mixed Group',
        order: 4,
        fields: [
          makeExtraField({ apiName: 'fs-hidden', name: 'FS Hidden', value: 'stale', isHidden: true, order: 3 }),
          makeExtraField({ apiName: 'fs-visible', name: 'FS Visible', value: 'ok', isHidden: false, order: 2 }),
          makeExtraField({ apiName: 'fs-undef', name: 'FS Undef', value: 'ok2', isHidden: undefined, order: 1 }),
        ],
      });

      render(
        React.createElement(KickoffOutputs, {
          viewMode: EKickoffOutputsViewModes.Short,
          outputs,
          fieldsets: [fieldset],
        }),
      );

      expect(screen.queryByTestId('text-output-plain-hidden')).not.toBeInTheDocument();
      expect(screen.queryByTestId('text-output-fs-hidden')).not.toBeInTheDocument();

      expect(screen.getByText('Mixed Group')).toBeInTheDocument();
      expect(screen.getByTestId('text-output-plain-visible')).toBeInTheDocument();
      expect(screen.getByTestId('text-output-plain-undef')).toBeInTheDocument();
      expect(screen.getByTestId('text-output-fs-visible')).toBeInTheDocument();
      expect(screen.getByTestId('text-output-fs-undef')).toBeInTheDocument();
    });

    it('hides fieldset header when all its fields have isHidden=true', () => {
      const hiddenFieldset = makeFieldsetRuntime({
        apiNameBinding: 'fs-all-hidden',
        title: 'All Hidden Title',
        description: 'All Hidden Description',
        order: 2,
        fields: [makeExtraField({ apiName: 'fs-h1', name: 'Hidden', value: 'stale', isHidden: true })],
      });
      const visibleField = makeExtraField({ apiName: 'plain-ok', name: 'Plain OK', value: 'shown', order: 1 });

      render(
        React.createElement(KickoffOutputs, {
          viewMode: EKickoffOutputsViewModes.Short,
          outputs: [visibleField],
          fieldsets: [hiddenFieldset],
        }),
      );

      expect(screen.queryByText('All Hidden Title')).not.toBeInTheDocument();
      expect(screen.queryByText('All Hidden Description')).not.toBeInTheDocument();
      expect(screen.queryByTestId('text-output-fs-h1')).not.toBeInTheDocument();
      expect(screen.getByTestId('text-output-plain-ok')).toBeInTheDocument();
    });

    it('excludes attachments from hidden file fields in isOnlyAttachmentsShown mode', () => {
      const hiddenAttachment = { id: 'h-1', url: 'hidden.pdf', name: 'hidden.pdf', size: 10 };
      const visibleAttachment = { id: 'v-1', url: 'visible.pdf', name: 'visible.pdf', size: 20 };
      const hiddenFsAttachment = { id: 'h-2', url: 'hidden-fs.pdf', name: 'hidden-fs.pdf', size: 30 };

      const outputs = [
        makeExtraField({
          apiName: 'file-hidden',
          type: EExtraFieldType.File,
          isHidden: true,
          order: 3,
          attachments: [hiddenAttachment],
        }),
        makeExtraField({
          apiName: 'file-visible',
          type: EExtraFieldType.File,
          isHidden: false,
          order: 2,
          attachments: [visibleAttachment],
        }),
      ];
      const fieldset = makeFieldsetRuntime({
        apiNameBinding: 'fs-files',
        order: 1,
        fields: [
          makeExtraField({
            apiName: 'fs-file-hidden',
            type: EExtraFieldType.File,
            isHidden: true,
            attachments: [hiddenFsAttachment],
          }),
        ],
      });

      render(
        React.createElement(KickoffOutputs, {
          ...baseProps,
          outputs,
          fieldsets: [fieldset],
        }),
      );

      expect(Attachments as jest.Mock).toHaveBeenCalledTimes(1);
      expect(getAttachmentsProps()).toEqual([visibleAttachment]);
    });

    it('skips hidden field with highest order and shows first visible field in isTruncated mode', () => {
      const outputs = [
        makeExtraField({ apiName: 'top-hidden', name: 'Top Hidden', value: 'stale', isHidden: true, order: 10 }),
        makeExtraField({ apiName: 'next-visible', name: 'Next Visible', value: 'shown', isHidden: false, order: 5 }),
      ];

      render(
        React.createElement(KickoffOutputs, {
          viewMode: EKickoffOutputsViewModes.Short,
          outputs,
          fieldsets: [],
          isTruncated: true,
        }),
      );

      expect(screen.queryByTestId('text-output-top-hidden')).not.toBeInTheDocument();
      expect(screen.getByTestId('text-output-next-visible')).toBeInTheDocument();
    });

    it('keeps Kickoff header and Edit button in Detailed mode when all fields are hidden', () => {
      const onEdit = jest.fn();
      const outputs = [
        makeExtraField({ apiName: 'only-hidden', name: 'Only Hidden', value: 'stale', isHidden: true, order: 1 }),
      ];

      render(
        React.createElement(KickoffOutputs, {
          viewMode: EKickoffOutputsViewModes.Detailed,
          outputs,
          fieldsets: [],
          onEdit,
        }),
      );

      expect(screen.getByText(KICKOFF_TITLE)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: EDIT_KICKOFF_LABEL })).toBeInTheDocument();
      expect(screen.queryByTestId('text-output-only-hidden')).not.toBeInTheDocument();
    });
  });
});
