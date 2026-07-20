import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { intlMock } from '../../../../__stubs__/intlMock';
import { makeExtraField } from '../../../../__stubs__/fields.factory';
import { makeFieldsetBindingClient, makeFieldsetField } from '../../../../__stubs__/fieldsets.factory';
import {
  IExtraField,
  IKickoffClient,
  ITemplateClient,
} from '../../../../types/template';
import { IFieldsetCatalogItem } from '../../../../types/fieldset';
import { ETemplateStatus } from '../../../../types/redux';

jest.mock('../../../../redux/selectors/fieldsets', () => ({
  getFieldsetsCatalogIsLoading: jest.fn(() => false),
}));

jest.mock('../../../../redux/actions', () => ({
  patchTemplate: jest.fn((payload: unknown) => ({ type: 'PATCH_TEMPLATE', payload })),
}));

jest.mock('../../../../hooks/useHashLink', () => ({
  useHashLink: jest.fn(),
}));

jest.mock('../../TaskForm/utils/getTaskVariables', () => ({
  useWorkflowNameVariables: jest.fn(() => []),
}));

jest.mock('../../ExtraFields/utils/useDatasetOptions', () => ({
  useDatasetOptions: jest.fn(() => []),
}));

jest.mock('../utils/getEmptyField', () => ({
  getEmptyField: jest.fn(),
}));

jest.mock('../../ExtraFields/utils/ExtraFieldsMap', () => ({
  ExtraFieldsMap: [{ id: 'string', label: 'String' }],
}));

jest.mock('../../ExtraFields/utils/ExtraFieldIcon', () => ({
  ExtraFieldIcon: (props: { id: string; onClick: () => void }) =>
    React.createElement(
      'button',
      { type: 'button', onClick: props.onClick },
      `Add field ${props.id}`,
    ),
}));

jest.mock('../../ExtraFields/utils/ExtraFieldsLabels', () => ({
  ExtraFieldsLabels: (props: { extraFields: { apiName: string }[] }) =>
    React.createElement(
      'div',
      { 'data-testid': 'extra-fields-labels' },
      props.extraFields.map((f) =>
        React.createElement('span', { key: f.apiName }, f.apiName),
      ),
    ),
}));

jest.mock('../../TaskOutputFlow/FieldsetIconPicker', () => ({
  FieldsetIconPicker: (props: {
    selectedFieldsetIds: number[];
    onSelectFieldset: (item: IFieldsetCatalogItem) => void;
    onRemoveFieldset: (sharedFieldsetId: number) => void;
  }) =>
    React.createElement(
      'div',
      { 'data-testid': 'fieldset-icon-picker' },
      React.createElement(
        'button',
        {
          type: 'button',
          'data-testid': 'add-fieldset-btn',
          onClick: () =>
            props.onSelectFieldset({
              id: 200,
              apiName: 'fs-new',
              name: 'New Set',
              description: '',
              fields: [],
              rules: [],
              order: 0,
              labelPosition: 'top',
              layout: 'vertical',
              title: '',
            } as IFieldsetCatalogItem),
        },
        'Add fieldset New Set',
      ),
    ),
}));

jest.mock('../../TaskOutputFlow/MergedOutputRows', () => ({
  MergedOutputRows: () =>
    React.createElement('div', { 'data-testid': 'merged-rows' }),
}));

jest.mock('../../FieldsetOutputsPreview/FieldsetOutputsPreview', () => ({
  FieldsetOutputsPreview: (props: {
    fieldsets: { apiNameBinding: string; fields?: unknown[] }[];
  }) => {
    const groups = props.fieldsets.filter(
      (fieldset) => fieldset.fields && fieldset.fields.length > 0,
    );
    if (!groups.length) return null;
    return React.createElement(
      'div',
      { 'data-testid': 'fieldset-outputs-preview' },
      groups.map((fieldset) =>
        React.createElement('span', { key: fieldset.apiNameBinding }, fieldset.apiNameBinding),
      ),
    );
  },
}));

jest.mock('../KickoffMenu', () => ({
  KickoffMenu: (props: {
    isKickoffOpen: boolean;
    isClearDisabled: boolean;
    toggleKickoff: () => void;
    clearForm: () => void;
  }) =>
    React.createElement(
      'div',
      null,
      React.createElement(
        'button',
        {
          type: 'button',
          'data-testid': 'kickoff-toggle',
          onClick: props.toggleKickoff,
        },
        props.isKickoffOpen ? 'Close' : 'Open',
      ),
      React.createElement(
        'button',
        {
          type: 'button',
          'data-testid': 'kickoff-clear',
          disabled: props.isClearDisabled,
          onClick: props.clearForm,
        },
        'Clear',
      ),
    ),
}));

jest.mock('../KickoffShareForm', () => ({
  KickoffShareForm: () => null,
}));

jest.mock('../../InputWithVariables', () => ({
  InputWithVariables: () => null,
}));

jest.mock('../../../IntlMessages', () => ({
  IntlMessages: (props: { id: string }) =>
    React.createElement('span', null, props.id),
}));

import { KickoffRedux } from '../KickoffRedux';
import { getEmptyField } from '../utils/getEmptyField';
import { useSelector } from 'react-redux';
import {
  getFieldsetsCatalogIsLoading,
} from '../../../../redux/selectors/fieldsets';

describe('KickoffRedux', () => {
  const makeField = (overrides: Partial<IExtraField> = {}) => makeExtraField({
    name: 'Field 1',
    ...overrides,
  });

  const makeKickoff = (overrides: Partial<IKickoffClient> = {}): IKickoffClient => ({
    description: '',
    fields: [],
    fieldsets: [],
    ...overrides,
  });

  const makeTemplate = (kickoff: IKickoffClient): ITemplateClient => ({
    id: 1,
    kickoff,
    wfNameTemplate: '',
  } as unknown as ITemplateClient);

  const NEW_FIELD: IExtraField = makeExtraField({
    apiName: 'new-field',
    name: 'New Field',
    order: -1,
  });

  const renderKickoff = (params: {
    kickoff: IKickoffClient;
    setKickoff?: jest.Mock;
  }) => {
    const setKickoff = params.setKickoff ?? jest.fn();

    (getFieldsetsCatalogIsLoading as jest.Mock).mockReturnValue(false);

    render(
      React.createElement(KickoffRedux, {
        template: makeTemplate(params.kickoff),
        intl: intlMock,
        accountId: 1,
        templateStatus: ETemplateStatus.Saved,
        setKickoff,
      }),
    );
    return { setKickoff };
  };

  const EMPTY_STATE = {};

  beforeEach(() => {
    jest.clearAllMocks();
    (getEmptyField as jest.Mock).mockReturnValue(NEW_FIELD);
    (useSelector as jest.Mock).mockImplementation((selector: unknown) =>
      (selector as (s: unknown) => unknown)(EMPTY_STATE),
    );
  });

  describe('collapsed kickoff: labels block', () => {
    it('renders FieldsetOutputsPreview when a fieldset binding has fields', () => {
      renderKickoff({
        kickoff: makeKickoff({
          fieldsets: [makeFieldsetBindingClient({
            apiNameBinding: 'fs-1',
            order: 0,
            fields: [makeFieldsetField({ apiName: 'fs-field-1' })],
          })],
        }),
      });

      expect(screen.getByTestId('fieldset-outputs-preview')).toBeInTheDocument();
      expect(screen.queryByTestId('extra-fields-labels')).not.toBeInTheDocument();
    });

    it('renders no labels block at all when no own fields and fieldset binding has empty fields', () => {
      renderKickoff({
        kickoff: makeKickoff({
          fieldsets: [makeFieldsetBindingClient({ apiNameBinding: 'fs-1', order: 0 })],
        }),
      });

      expect(screen.queryByTestId('fieldset-outputs-preview')).not.toBeInTheDocument();
      expect(screen.queryByTestId('extra-fields-labels')).not.toBeInTheDocument();
      expect(screen.getAllByRole('button', { name: 'Toggle expand' })).toHaveLength(1);
    });
  });

  describe('expanded kickoff: isFormEmpty accounts for fieldsets', () => {
    it('renders MergedOutputRows when only fieldsets are present (no own fields or description)', () => {
      renderKickoff({
        kickoff: makeKickoff({
          fieldsets: [makeFieldsetBindingClient({ apiNameBinding: 'fs-1', order: 0 })],
        }),
      });

      userEvent.click(screen.getByTestId('kickoff-toggle'));

      expect(screen.getByTestId('merged-rows')).toBeInTheDocument();
    });
  });

  describe('add fieldset', () => {
    it('calls setKickoff with the new fieldset added to the array', () => {
      const { setKickoff } = renderKickoff({
        kickoff: makeKickoff(),
      });

      userEvent.click(screen.getByTestId('kickoff-toggle'));
      userEvent.click(screen.getByTestId('add-fieldset-btn'));

      expect(setKickoff).toHaveBeenCalledTimes(1);
      expect(setKickoff).toHaveBeenCalledWith(
        expect.objectContaining({
          fieldsets: expect.arrayContaining([
            expect.objectContaining({ sharedFieldsetId: 200 }),
          ]),
        }),
      );
    });
  });

  describe('create field when fieldsets are connected', () => {
    it('calls setKickoff with updated fields AND fieldset order patches', () => {
      const { setKickoff } = renderKickoff({
        kickoff: makeKickoff({
          fieldsets: [makeFieldsetBindingClient({ apiNameBinding: 'fs-1', order: 0 })],
        }),
      });

      userEvent.click(screen.getByTestId('kickoff-toggle'));
      userEvent.click(screen.getByRole('button', { name: 'Add field string' }));

      expect(setKickoff).toHaveBeenCalledTimes(1);
      expect(setKickoff).toHaveBeenCalledWith(
        expect.objectContaining({
          fields: expect.arrayContaining([
            expect.objectContaining({ apiName: 'new-field' }),
          ]),
          fieldsets: expect.arrayContaining([
            expect.objectContaining({ apiNameBinding: 'fs-1' }),
          ]),
        }),
      );
    });
  });

  it('keeps hook order stable when the template becomes unavailable', () => {
    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => undefined);
    const view = render(
      <KickoffRedux
        template={makeTemplate(makeKickoff())}
        intl={intlMock}
        accountId={1}
        setKickoff={jest.fn()}
      />,
    );

    expect(() => view.rerender(<KickoffRedux />)).toThrow(
      'KickoffRedux must receive a template prop or be used inside the Edit Template form provider',
    );
    expect(consoleError.mock.calls.flat().join(' ')).not.toContain('Rendered fewer hooks');
    consoleError.mockRestore();
  });

  describe('clear kickoff', () => {
    it('calls setKickoff with empty fields AND empty fieldsets', () => {
      const { setKickoff } = renderKickoff({
        kickoff: makeKickoff({
          fields: [makeField({ apiName: 'f-1' })],
          fieldsets: [makeFieldsetBindingClient({ apiNameBinding: 'fs-1', order: 0 })],
          description: 'desc',
        }),
      });

      userEvent.click(screen.getByTestId('kickoff-clear'));

      expect(setKickoff).toHaveBeenCalledTimes(1);
      expect(setKickoff).toHaveBeenCalledWith(
        expect.objectContaining({
          fields: [],
          fieldsets: [],
          description: '',
        }),
      );
    });
  });
});
