// <reference types="jest" />
import * as React from 'react';
import { render } from '@testing-library/react';

import { KickoffOutputs, EKickoffOutputsViewModes } from '../KickoffOutputs';
import { EExtraFieldType, IExtraField, IFieldsetData } from '../../../types/template';
import { Attachments } from '../../Attachments';

jest.mock('../../Attachments', () => ({
  Attachments: jest.fn(() => null),
}));

jest.mock('../CheckboxOutput', () => ({ CheckboxOutput: () => null }));
jest.mock('../RadioOutput', () => ({ RadioOutput: () => null }));
jest.mock('../TextOutput', () => ({ TextOutput: () => null }));
jest.mock('../UrlOutput', () => ({ UrlOutput: () => null }));
jest.mock('../FileOutput', () => ({ FileOutput: () => null }));
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
