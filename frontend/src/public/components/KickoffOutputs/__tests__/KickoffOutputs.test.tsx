import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { KickoffOutputs, EKickoffOutputsViewModes } from '../KickoffOutputs';
import { makeExtraField } from '../../../__stubs__/fields.factory';
import { makeFieldsetRuntime } from '../../../__stubs__/fieldsets.factory';
import { EExtraFieldType, IExtraField } from '../../../types/template';
import { Attachments } from '../../Attachments';

type TOutputMockProps = Pick<IExtraField, 'apiName' | 'name'>;

jest.mock('../../Attachments', () => ({
  Attachments: jest.fn(() => null),
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
    const { container } = render(React.createElement(KickoffOutputs, {
      viewMode: EKickoffOutputsViewModes.Detailed,
      outputs: [],
      fieldsets: [],
    }));

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

    render(React.createElement(KickoffOutputs, {
      viewMode: EKickoffOutputsViewModes.Short,
      outputs: [fieldA, fieldB],
      fieldsets: [fsM, fsN],
    }));

    const rendered = screen.getAllByTestId(/^text-output-/);
    expect(rendered.map((el) => el.getAttribute('data-testid'))).toEqual([
      'text-output-fb',
      'text-output-fs-m-1',
      'text-output-fs-n-1',
      'text-output-fa',
    ]);
  });

  it('in full mode renders fieldset group: name, description and only non-empty fields', () => {
    const fieldset = makeFieldsetRuntime({
      name: 'Contacts',
      description: 'Reachout details',
      order: 1,
      fields: [
        makeExtraField({ apiName: 'email', name: 'Email', value: 'a@b.com', order: 1 }),
        makeExtraField({ apiName: 'phone', name: 'Phone', order: 2 }),
        makeExtraField({ apiName: 'city', name: 'City', value: 'NY', order: 3 }),
      ],
    });

    render(React.createElement(KickoffOutputs, {
      viewMode: EKickoffOutputsViewModes.Short,
      outputs: [],
      fieldsets: [fieldset],
    }));

    expect(screen.getByText('Contacts')).toBeInTheDocument();
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
      attachments: [{ id: 1, url: 'doc.pdf', name: 'doc.pdf', size: 10 }],
    });

    const fieldset = makeFieldsetRuntime({
      name: 'Docs',
      fields: [fileField],
    });

    render(React.createElement(KickoffOutputs, {
      viewMode: EKickoffOutputsViewModes.Short,
      outputs: [],
      fieldsets: [fieldset],
    }));

    expect(screen.getByTestId('file-output-doc')).toBeInTheDocument();
  });

  it('in truncated mode renders fieldset group title and only the first field', () => {
    const fieldset = makeFieldsetRuntime({
      name: 'Profile',
      order: 5,
      fields: [
        makeExtraField({ apiName: 'first', name: 'First', value: 'one' }),
        makeExtraField({ apiName: 'second', name: 'Second', value: 'two' }),
        makeExtraField({ apiName: 'third', name: 'Third', value: 'three' }),
      ],
    });

    render(React.createElement(KickoffOutputs, {
      viewMode: EKickoffOutputsViewModes.Short,
      outputs: [],
      fieldsets: [fieldset],
      isTruncated: true,
    }));

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
      render(React.createElement(KickoffOutputs, {
        viewMode: EKickoffOutputsViewModes.Short,
        outputs: [],
        fieldsets: [fieldset],
        isTruncated: true,
      })),
    ).not.toThrow();

    expect(screen.queryByTestId(/^text-output-/)).toBeNull();
    expect(screen.queryByTestId(/^file-output-/)).toBeNull();
  });

  describe('isOnlyAttachmentsShown — collecting attachments from fieldsets', () => {
    it('collects file attachments from both outputs and fieldsets respecting order', () => {
      const attachment1 = { id: 1, url: 'file1.pdf', name: 'file1.pdf', size: 100 };
      const attachment2 = { id: 2, url: 'file2.png', name: 'file2.png', size: 200 };
      const attachment3 = { id: 3, url: 'file3.doc', name: 'file3.doc', size: 300 };

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

      render(React.createElement(KickoffOutputs, {
        ...baseProps,
        outputs: [stringOutput, fileOutput],
        fieldsets: [fieldset],
      }));

      expect(Attachments as jest.Mock).toHaveBeenCalledTimes(1);

      const attachments = getAttachmentsProps();
      expect(attachments).toEqual([attachment1, attachment2, attachment3]);
    });
  });
});
