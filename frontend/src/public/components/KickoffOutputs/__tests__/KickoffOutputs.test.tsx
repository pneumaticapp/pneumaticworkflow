// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { KickoffOutputs, EKickoffOutputsViewModes } from '../KickoffOutputs';
import { EExtraFieldType, IExtraField, IFieldsetData } from '../../../types/template';
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

  const makeField = (overrides: Partial<IExtraField> = {}): IExtraField => ({
    apiName: `field-${Math.random()}`,
    name: 'Field',
    type: EExtraFieldType.String,
    order: 0,
    userId: null,
    groupId: null,
    ...overrides,
  });

  const makeFieldset = (overrides: Partial<IFieldsetData> = {}): IFieldsetData => ({
    id: Math.floor(Math.random() * 1000),
    apiName: `fieldset-${Math.random()}`,
    name: 'Fieldset',
    description: '',
    order: 0,
    fields: [],
    ...overrides,
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
    const fieldA = makeField({ apiName: 'fa', order: 1, value: 'av' });
    const fieldB = makeField({ apiName: 'fb', order: 4, value: 'bv' });
    const fsM = makeFieldset({
      apiName: 'fs-m',
      order: 3,
      fields: [makeField({ apiName: 'fs-m-1', value: 'mv' })],
    });
    const fsN = makeFieldset({
      apiName: 'fs-n',
      order: 2,
      fields: [makeField({ apiName: 'fs-n-1', value: 'nv' })],
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
    const fieldset = makeFieldset({
      name: 'Contacts',
      description: 'Reachout details',
      order: 1,
      fields: [
        makeField({ apiName: 'email', name: 'Email', value: 'a@b.com', order: 1 }),
        makeField({ apiName: 'phone', name: 'Phone', value: '', order: 2 }),
        makeField({ apiName: 'city', name: 'City', value: 'NY', order: 3 }),
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
    const fileField = makeField({
      apiName: 'doc',
      name: 'Document',
      type: EExtraFieldType.File,
      value: null,
      attachments: [{ id: 1, url: 'doc.pdf', name: 'doc.pdf', size: 10 }],
    });

    const fieldset = makeFieldset({
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
    const fieldset = makeFieldset({
      name: 'Profile',
      order: 5,
      fields: [
        makeField({ apiName: 'first', name: 'First', value: 'one' }),
        makeField({ apiName: 'second', name: 'Second', value: 'two' }),
        makeField({ apiName: 'third', name: 'Third', value: 'three' }),
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
    const fieldset = makeFieldset({
      name: 'Empty Group',
      order: 1,
      fields: [],
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

      const fileOutput = makeField({
        type: EExtraFieldType.File,
        order: 2,
        attachments: [attachment1],
      });

      const stringOutput = makeField({
        type: EExtraFieldType.String,
        order: 0,
        value: 'some text',
      });

      const fieldset = makeFieldset({
        order: 1,
        fields: [
          makeField({ type: EExtraFieldType.File, attachments: [attachment2] }),
          makeField({ type: EExtraFieldType.String, value: 'ignored' }),
          makeField({ type: EExtraFieldType.File, attachments: [attachment3] }),
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
