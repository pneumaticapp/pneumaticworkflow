import * as React from 'react';
import { render } from '@testing-library/react';
import { IntlProvider } from 'react-intl';
import { enMessages } from '../../../../lang/locales/en_US';

import { ExtraFieldIntl } from '../index';
import { ExtraFieldDropdown } from '../utils/ExtraFieldDropdown';
import { EExtraFieldMode, EExtraFieldType } from '../../../../types/template';

jest.mock('react-redux', () => ({
  useSelector: jest.fn((selector) => {
    const mockState = {
      datasets: {
        allDatasetsList: [],
        isAllDatasetsLoading: false,
        isAllDatasetsLoaded: false,
      },
    };

    return selector(mockState);
  }),
  useDispatch: jest.fn(() => jest.fn()),
}));

jest.mock('../utils/ExtraFieldDropdown', () => ({
  ExtraFieldDropdown: jest.fn(() => null),
}));

jest.mock('../String', () => ({ ExtraFieldString: () => <div /> }));
jest.mock('../Text', () => ({ ExtraFieldText: () => <div /> }));
jest.mock('../Url', () => ({ ExtraFieldUrl: () => <div /> }));
jest.mock('../Date', () => ({ ExtraFieldDate: () => <div /> }));
jest.mock('../Checkbox', () => ({ ExtraFieldCheckbox: () => <div /> }));
jest.mock('../Radio', () => ({ ExtraFieldRadio: () => <div /> }));
jest.mock('../Creatable', () => ({ ExtraFieldCreatable: () => <div /> }));
jest.mock('../File', () => ({ ExtraFieldFile: () => <div /> }));
jest.mock('../User', () => ({ ExtraFieldUser: () => <div /> }));
jest.mock('../Number', () => ({ ExtraFieldNumber: () => <div /> }));

const baseField = {
  apiName: 'f1',
  name: 'Field 1',
  type: EExtraFieldType.String,
  order: 0,
  userId: null,
  groupId: null,
};

const baseProps = {
  field: baseField,
  editField: jest.fn(),
  accountId: 1,
  showDropdown: true,
  mode: EExtraFieldMode.Kickoff,
};

const renderWithIntl = (ui: React.ReactElement) =>
  render(
    <IntlProvider locale="en" messages={enMessages}>
      {ui}
    </IntlProvider>,
  );

describe('ExtraField', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Passing isHidden to ExtraFieldDropdown', () => {
    it('passes isHidden=true to ExtraFieldDropdown', () => {
      renderWithIntl(
        <ExtraFieldIntl {...baseProps} field={{ ...baseField, isHidden: true }} />,
      );

      expect(ExtraFieldDropdown as jest.Mock).toHaveBeenCalledWith(
        expect.objectContaining({ isHidden: true }),
        {},
      );
    });

    it('passes isHidden=false by default when field has no isHidden', () => {
      renderWithIntl(
        <ExtraFieldIntl {...baseProps} field={{ ...baseField }} />,
      );

      expect(ExtraFieldDropdown as jest.Mock).toHaveBeenCalledWith(
        expect.objectContaining({ isHidden: false }),
        {},
      );
    });
  });
});
