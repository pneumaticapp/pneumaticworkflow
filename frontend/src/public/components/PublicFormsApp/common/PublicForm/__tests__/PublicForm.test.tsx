import * as React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch } from 'react-redux';

import { PublicForm } from '../PublicForm';
import { getPublicForm } from '../../../../../api/getPublicForm';
import { runPublicForm } from '../../../../../api/runPublicForm';
import { MergedOutputList } from '../../../../MergedOutputList';
import { NotificationManager } from '../../../../UI/Notifications';
import { makeExtraField } from '../../../../../__stubs__/fields.factory';
import { makeFieldsetData } from '../../../../../__stubs__/fieldsets.factory';
import { IExtraField, IFieldsetData } from '../../../../../types/template';
import { intlMock } from '../../../../../__stubs__/intlMock';

jest.mock('../../../../../api/getPublicForm', () => ({
  getPublicForm: jest.fn(),
}));

jest.mock('../../../../../api/runPublicForm', () => ({
  runPublicForm: jest.fn().mockResolvedValue({ redirectUrl: null }),
}));

jest.mock('../../../../../api/deleteRemovedFilesFromFields', () => ({
  deleteRemovedFilesFromFields: jest.fn().mockResolvedValue(undefined),
}));

jest.mock('../../../../../utils/mappers', () => ({
  getNormalizedKickoff: jest.fn((kickoff: { fields: IExtraField[] }) => {
    const result: Record<string, string> = {};
    for (const field of kickoff.fields) {
      result[field.apiName] = String(field.value || '');
    }
    return result;
  }),
}));

jest.mock('../../../../MergedOutputList', () => ({
  MergedOutputList: jest.fn(() => React.createElement('div', { 'data-testid': 'merged-output-list' })),
}));

jest.mock('../../../../UI/Buttons/Button', () => ({
  Button: (props: { label: string; disabled?: boolean; onClick?: () => void }) =>
    React.createElement('button', {
      type: 'button',
      disabled: props.disabled,
      onClick: props.onClick,
    }, props.label),
}));

jest.mock('../../../../UI/Typeography/Header', () => ({
  Header: ({ children }: { children: React.ReactNode }) =>
    React.createElement('h1', null, children),
}));

jest.mock('../../../../RichText', () => ({
  RichText: ({ text }: { text: string }) => React.createElement('span', null, text),
}));

jest.mock('../../Copyright', () => ({
  Copyright: () => null,
}));

jest.mock('../../FormSkeleton', () => ({
  FormSkeleton: () => React.createElement('div', { 'data-testid': 'skeleton' }),
}));

jest.mock('../../../../../utils/getConfig', () => ({
  getPublicFormConfig: () => ({
    config: { recaptchaSecret: 'test-secret' },
  }),
  getBrowserConfigEnv: () => ({
    api: { urls: {} },
  }),
}));

jest.mock('react-google-recaptcha', () => ({
  __esModule: true,
  default: () => null,
}));

jest.mock('../../../../../constants/enviroment', () => ({
  isEnvCaptcha: false,
}));

jest.mock('../../../../../hooks/useShouldHideIntercom', () => ({
  useShouldHideIntercom: jest.fn(),
}));

jest.mock('../../../../../utils/logger', () => ({
  logger: { error: jest.fn(), info: jest.fn() },
}));

jest.mock('../../../../UI/Notifications', () => ({
  NotificationManager: { notifyApiError: jest.fn(), success: jest.fn(), warning: jest.fn() },
}));

const formatMsg = (id: string) => intlMock.formatMessage({ id });
const SUBMIT_LABEL = formatMsg('public-form.launch');

const makePublicFormResponse = (overrides: {
  fields?: IExtraField[];
  fieldsets?: IFieldsetData[];
} = {}) => ({
  accountId: 1,
  name: 'Test Form',
  description: '',
  showCaptcha: false,
  kickoff: {
    description: '',
    fields: overrides.fields || [],
    fieldsets: overrides.fieldsets || [],
  },
});

const getLastMergedOutputListProps = () => {
  const mock = MergedOutputList as jest.Mock;
  return mock.mock.calls[mock.mock.calls.length - 1][0] as {
    fields: IExtraField[];
    fieldsets: IFieldsetData[];
    onEditField: (apiName: string) => (changedProps: Partial<IExtraField>) => void;
    onEditFieldsetField: (apiName: string) => (changedProps: Partial<IExtraField>) => void;
  };
};

describe('PublicForm', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as jest.Mock).mockReturnValue(jest.fn());
  });

  describe('Filtering fields by isHidden', () => {
    it('renders only visible fields from a mixed list', async () => {
      (getPublicForm as jest.Mock).mockResolvedValue(
        makePublicFormResponse({
          fields: [
            makeExtraField({ apiName: 'f1', isHidden: true }),
            makeExtraField({ apiName: 'f2', isHidden: false }),
            makeExtraField({ apiName: 'f3' }),
          ],
        }),
      );

      render(React.createElement(PublicForm, { type: 'shared' }));

      await waitFor(() => {
        expect(MergedOutputList).toHaveBeenCalled();
      });

      const props = getLastMergedOutputListProps();
      expect(props.fields).toHaveLength(2);
      expect(props.fields.map((field: IExtraField) => field.apiName)).toEqual(
        expect.arrayContaining(['f2', 'f3']),
      );
    });
  });

  describe('Fieldsets: rendering', () => {
    it('passes fieldsets to MergedOutputList', async () => {
      const fieldset = makeFieldsetData({
        fields: [makeExtraField({ apiName: 'fs-field-1', order: 1 })],
        order: 1,
      });

      (getPublicForm as jest.Mock).mockResolvedValue(
        makePublicFormResponse({
          fields: [makeExtraField({ apiName: 'k1', order: 0 })],
          fieldsets: [fieldset],
        }),
      );

      render(React.createElement(PublicForm, { type: 'shared' }));

      await waitFor(() => {
        expect(MergedOutputList).toHaveBeenCalled();
      });

      expect(MergedOutputList).toHaveBeenCalledTimes(1);
      expect(MergedOutputList).toHaveBeenCalledWith(
        expect.objectContaining({
          fieldsets: expect.arrayContaining([
            expect.objectContaining({ apiName: 'fs-1' }),
          ]),
        }),
        expect.anything(),
      );
    });
  });

  describe('Fieldsets: isHidden filtering', () => {
    it('filters out isHidden fields inside fieldsets', async () => {
      const fieldset = makeFieldsetData({
        fields: [
          makeExtraField({ apiName: 'fs-hidden', isHidden: true, order: 1 }),
          makeExtraField({ apiName: 'fs-visible', isHidden: false, order: 2 }),
          makeExtraField({ apiName: 'fs-default', order: 3 }),
        ],
        order: 1,
      });

      (getPublicForm as jest.Mock).mockResolvedValue(
        makePublicFormResponse({ fieldsets: [fieldset] }),
      );

      render(React.createElement(PublicForm, { type: 'shared' }));

      await waitFor(() => {
        expect(MergedOutputList).toHaveBeenCalled();
      });

      const props = getLastMergedOutputListProps();
      const fieldsetFields = props.fieldsets[0].fields;
      expect(fieldsetFields).toHaveLength(2);
      expect(fieldsetFields.map((field: IExtraField) => field.apiName)).toEqual(
        expect.arrayContaining(['fs-visible', 'fs-default']),
      );
    });
  });

  describe('Fieldsets: validation', () => {
    it('disables Submit when fieldset has an empty required field', async () => {
      (getPublicForm as jest.Mock).mockResolvedValue(
        makePublicFormResponse({
          fields: [makeExtraField({ apiName: 'k1', value: 'filled' })],
          fieldsets: [
            makeFieldsetData({
              fields: [makeExtraField({ apiName: 'fs-req', isRequired: true, value: '', order: 1 })],
              order: 1,
            }),
          ],
        }),
      );

      render(React.createElement(PublicForm, { type: 'shared' }));

      const submitButton = await screen.findByRole('button', { name: SUBMIT_LABEL });
      expect(submitButton).toBeDisabled();
    });

    it('enables Submit when all required fieldset fields are filled', async () => {
      (getPublicForm as jest.Mock).mockResolvedValue(
        makePublicFormResponse({
          fields: [makeExtraField({ apiName: 'k1', value: 'filled' })],
          fieldsets: [
            makeFieldsetData({
              fields: [makeExtraField({ apiName: 'fs-req', isRequired: true, value: 'also filled', order: 1 })],
              order: 1,
            }),
          ],
        }),
      );

      render(React.createElement(PublicForm, { type: 'shared' }));

      const submitButton = await screen.findByRole('button', { name: SUBMIT_LABEL });
      expect(submitButton).not.toBeDisabled();
    });

    it('disables Submit when one of multiple fieldsets has an empty required field', async () => {
      (getPublicForm as jest.Mock).mockResolvedValue(
        makePublicFormResponse({
          fieldsets: [
            makeFieldsetData({
              id: 1,
              apiName: 'fs-ok',
              fields: [makeExtraField({ apiName: 'ok-field', isRequired: true, value: 'filled', order: 1 })],
              order: 1,
            }),
            makeFieldsetData({
              id: 2,
              apiName: 'fs-bad',
              fields: [makeExtraField({ apiName: 'bad-field', isRequired: true, value: '', order: 1 })],
              order: 2,
            }),
          ],
        }),
      );

      render(React.createElement(PublicForm, { type: 'shared' }));

      const submitButton = await screen.findByRole('button', { name: SUBMIT_LABEL });
      expect(submitButton).toBeDisabled();
    });
  });

  describe('Fieldsets: submit', () => {
    it('sends fieldset fields merged into kickoff on submit', async () => {
      (getPublicForm as jest.Mock).mockResolvedValue(
        makePublicFormResponse({
          fields: [makeExtraField({ apiName: 'k1', value: 'kickoff-val' })],
          fieldsets: [
            makeFieldsetData({
              fields: [makeExtraField({ apiName: 'fs1', value: 'fs-val', order: 1 })],
              order: 1,
            }),
          ],
        }),
      );

      render(React.createElement(PublicForm, { type: 'shared' }));

      const submitButton = await screen.findByRole('button', { name: SUBMIT_LABEL });
      userEvent.click(submitButton);

      await waitFor(() => {
        expect(runPublicForm).toHaveBeenCalledTimes(1);
      });

      expect(runPublicForm).toHaveBeenCalledWith(
        '',
        expect.objectContaining({
          'k1': 'kickoff-val',
          'fs1': 'fs-val',
        }),
      );
    });
  });

  describe('Fieldsets: editing', () => {
    it('updates fieldset field value via onEditFieldsetField', async () => {
      (getPublicForm as jest.Mock).mockResolvedValue(
        makePublicFormResponse({
          fieldsets: [
            makeFieldsetData({
              fields: [makeExtraField({ apiName: 'fs-edit-1', value: 'old-value', order: 1 })],
              order: 1,
            }),
          ],
        }),
      );

      render(React.createElement(PublicForm, { type: 'shared' }));

      await waitFor(() => {
        expect(MergedOutputList).toHaveBeenCalled();
      });

      const props = getLastMergedOutputListProps();

      act(() => {
        props.onEditFieldsetField('fs-edit-1')({ value: 'new-value' });
      });

      const submitButton = screen.getByRole('button', { name: SUBMIT_LABEL });
      userEvent.click(submitButton);

      await waitFor(() => {
        expect(runPublicForm).toHaveBeenCalledTimes(1);
      });

      expect(runPublicForm).toHaveBeenCalledWith(
        '',
        expect.objectContaining({
          'fs-edit-1': 'new-value',
        }),
      );
    });
  });

  describe('Submit: error handling', () => {
    it('forwards backend validation error message to notification', async () => {
      const backendError = {
        code: 'validation_error',
        message: 'The sum of the fields in this field set must equal "6"',
      };

      (getPublicForm as jest.Mock).mockResolvedValue(
        makePublicFormResponse({
          fields: [makeExtraField({ apiName: 'k1', value: 'filled' })],
        }),
      );
      (runPublicForm as jest.Mock).mockRejectedValue(backendError);

      render(React.createElement(PublicForm, { type: 'shared' }));

      const submitButton = await screen.findByRole('button', { name: SUBMIT_LABEL });
      userEvent.click(submitButton);

      await waitFor(() => {
        expect(NotificationManager.notifyApiError).toHaveBeenCalledTimes(1);
      });

      expect(NotificationManager.notifyApiError).toHaveBeenCalledWith(
        backendError,
        expect.objectContaining({
          message: 'The sum of the fields in this field set must equal "6"',
        }),
      );
    });
  });
});
