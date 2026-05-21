// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { intlMock } from '../../../../__stubs__/intlMock';
import {
  EExtraFieldType,
  IExtraField,
  IFieldsetData,
  IKickoff,
  ITemplate,
} from '../../../../types/template';
import { ETemplateStatus } from '../../../../types/redux';

jest.mock('../../../../redux/selectors/fieldsets', () => ({
  getFieldsetsCatalogByApiName: jest.fn(),
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
    fieldsetsByApiName: ReadonlyMap<string, IFieldsetData>;
    selectedFieldsetApiNames: string[];
    onSelectFieldset: (apiName: string) => void;
    onRemoveFieldset: (apiName: string) => void;
  }) =>
    React.createElement(
      'div',
      null,
      Array.from(props.fieldsetsByApiName.entries()).map(([apiName, fs]) =>
        React.createElement(
          'button',
          {
            key: `add-${apiName}`,
            type: 'button',
            onClick: () => props.onSelectFieldset(apiName),
          },
          `Add fieldset ${fs.name}`,
        ),
      ),
    ),
}));

jest.mock('../../TaskOutputFlow/MergedOutputRows', () => ({
  MergedOutputRows: () =>
    React.createElement('div', { 'data-testid': 'merged-rows' }),
}));

jest.mock('../../FieldsetOutputsPreview/FieldsetOutputsPreview', () => ({
  FieldsetOutputsPreview: (props: {
    fieldsets: { apiName: string }[];
    fieldsetsByApiName: ReadonlyMap<string, { fields: unknown[] }>;
  }) => {
    const groups = props.fieldsets
      .map((f) => {
        const data = props.fieldsetsByApiName.get(f.apiName);
        if (!data || !data.fields || data.fields.length === 0) return null;
        return f.apiName;
      })
      .filter((apiName): apiName is string => apiName !== null);
    if (!groups.length) return null;
    return React.createElement(
      'div',
      { 'data-testid': 'fieldset-outputs-preview' },
      groups.map((apiName) =>
        React.createElement('span', { key: apiName }, apiName),
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
  getFieldsetsCatalogByApiName,
  getFieldsetsCatalogIsLoading,
} from '../../../../redux/selectors/fieldsets';

describe('KickoffRedux', () => {
  const makeField = (overrides: Partial<IExtraField> = {}): IExtraField => ({
    apiName: 'f-1',
    name: 'Field 1',
    type: EExtraFieldType.String,
    order: 0,
    isRequired: false,
    isHidden: false,
    userId: null,
    groupId: null,
    description: '',
    selections: [],
    ...overrides,
  });

  const makeFieldsetData = (overrides: Partial<IFieldsetData> = {}): IFieldsetData => ({
    id: 1,
    apiName: 'fs-1',
    name: 'Fieldset 1',
    description: '',
    order: 0,
    fields: [],
    ...overrides,
  });

  const makeKickoff = (overrides: Partial<IKickoff> = {}): IKickoff => ({
    description: '',
    fields: [],
    fieldsets: [],
    ...overrides,
  });

  const makeTemplate = (kickoff: IKickoff): ITemplate => ({
    id: 1,
    kickoff,
    wfNameTemplate: '',
  } as unknown as ITemplate);

  const NEW_FIELD: IExtraField = {
    apiName: 'new-field',
    name: 'New Field',
    type: EExtraFieldType.String,
    order: -1,
    isRequired: false,
    isHidden: false,
    userId: null,
    groupId: null,
    description: '',
    selections: [],
  };

  const renderKickoff = (params: {
    kickoff: IKickoff;
    catalog?: ReadonlyMap<string, IFieldsetData>;
    setKickoff?: jest.Mock;
  }) => {
    const setKickoff = params.setKickoff ?? jest.fn();
    const catalog = params.catalog ?? new Map<string, IFieldsetData>();

    (getFieldsetsCatalogByApiName as jest.Mock).mockReturnValue(catalog);
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
    it('renders FieldsetOutputsPreview when a fieldset in catalog has fields', () => {
      const fsData = makeFieldsetData({
        apiName: 'fs-1',
        name: 'Set One',
        fields: [makeField({ apiName: 'fs-field-1' })],
      });
      renderKickoff({
        kickoff: makeKickoff({
          fieldsets: [{ apiName: 'fs-1', order: 0 }],
        }),
        catalog: new Map([['fs-1', fsData]]),
      });

      expect(screen.getByTestId('fieldset-outputs-preview')).toBeInTheDocument();
      expect(screen.queryByTestId('extra-fields-labels')).not.toBeInTheDocument();
    });

    it('renders no labels block at all when no own fields and catalog fieldset has empty fields', () => {
      const fsData = makeFieldsetData({ apiName: 'fs-1', fields: [] });
      renderKickoff({
        kickoff: makeKickoff({
          fieldsets: [{ apiName: 'fs-1', order: 0 }],
        }),
        catalog: new Map([['fs-1', fsData]]),
      });

      expect(screen.queryByTestId('fieldset-outputs-preview')).not.toBeInTheDocument();
      expect(screen.queryByTestId('extra-fields-labels')).not.toBeInTheDocument();
      expect(screen.getAllByRole('button', { name: 'Toggle expand' })).toHaveLength(1);
    });
  });

  describe('expanded kickoff: isFormEmpty accounts for fieldsets', () => {
    it('renders MergedOutputRows when only fieldsets are present (no own fields or description)', () => {
      const fsData = makeFieldsetData({ apiName: 'fs-1' });
      renderKickoff({
        kickoff: makeKickoff({
          fieldsets: [{ apiName: 'fs-1', order: 0 }],
        }),
        catalog: new Map([['fs-1', fsData]]),
      });

      userEvent.click(screen.getByTestId('kickoff-toggle'));

      expect(screen.getByTestId('merged-rows')).toBeInTheDocument();
    });
  });

  describe('add fieldset', () => {
    it('calls setKickoff with the new fieldset added to the array', () => {
      const fsData = makeFieldsetData({ apiName: 'fs-new', name: 'New Set' });
      const { setKickoff } = renderKickoff({
        kickoff: makeKickoff(),
        catalog: new Map([['fs-new', fsData]]),
      });

      userEvent.click(screen.getByTestId('kickoff-toggle'));
      userEvent.click(screen.getByRole('button', { name: 'Add fieldset New Set' }));

      expect(setKickoff).toHaveBeenCalledTimes(1);
      expect(setKickoff).toHaveBeenCalledWith(
        expect.objectContaining({
          fieldsets: expect.arrayContaining([
            expect.objectContaining({ apiName: 'fs-new' }),
          ]),
        }),
      );
    });

    it('does not call setKickoff when re-adding an already connected fieldset', () => {
      const fsData = makeFieldsetData({ apiName: 'fs-1' });
      const { setKickoff } = renderKickoff({
        kickoff: makeKickoff({
          fieldsets: [{ apiName: 'fs-1', order: 0 }],
        }),
        catalog: new Map([['fs-1', fsData]]),
      });

      userEvent.click(screen.getByTestId('kickoff-toggle'));
      userEvent.click(screen.getByRole('button', { name: 'Add fieldset Fieldset 1' }));

      expect(setKickoff).not.toHaveBeenCalled();
    });
  });

  describe('create field when fieldsets are connected', () => {
    it('calls setKickoff with updated fields AND fieldset order patches', () => {
      const fsData = makeFieldsetData({ apiName: 'fs-1' });
      const { setKickoff } = renderKickoff({
        kickoff: makeKickoff({
          fieldsets: [{ apiName: 'fs-1', order: 0 }],
        }),
        catalog: new Map([['fs-1', fsData]]),
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
            expect.objectContaining({ apiName: 'fs-1' }),
          ]),
        }),
      );
    });
  });

  describe('clear kickoff', () => {
    it('calls setKickoff with empty fields AND empty fieldsets', () => {
      const fsData = makeFieldsetData({ apiName: 'fs-1' });
      const { setKickoff } = renderKickoff({
        kickoff: makeKickoff({
          fields: [makeField({ apiName: 'f-1' })],
          fieldsets: [{ apiName: 'fs-1', order: 0 }],
          description: 'desc',
        }),
        catalog: new Map([['fs-1', fsData]]),
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
