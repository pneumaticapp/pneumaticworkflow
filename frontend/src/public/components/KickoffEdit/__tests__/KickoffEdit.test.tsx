import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { IntlProvider } from 'react-intl';
import { enMessages } from '../../../lang/locales/en_US';

import { EditKickoff } from '../KickoffEdit';
import { EExtraFieldType, IExtraField } from '../../../types/template';
import { MergedOutputList } from '../../MergedOutputList';

jest.mock('../../MergedOutputList', () => ({
  MergedOutputList: jest.fn(() => <div data-testid="merged-output-list" />),
}));

jest.mock('../../WorkflowEditPopup/utils/areKickoffFieldsValid', () => ({
  checkExtraFieldsAreValid: jest.fn(() => true),
}));

jest.mock('../../../utils/autoFocusFirstField', () => ({
  autoFocusFirstField: jest.fn(),
}));

jest.mock('../../UI/Loader', () => ({
  Loader: () => null,
}));

jest.mock('../../IntlMessages', () => ({
  IntlMessages: ({ id }: { id: string }) => <span>{id}</span>,
}));

jest.mock('../../UI/Buttons/Button', () => ({
  Button: () => <button />,
}));

const makeField = (apiName: string, order: number): IExtraField => ({
  apiName,
  name: apiName,
  type: EExtraFieldType.String,
  order,
  userId: null,
  groupId: null,
});

const baseProps = {
  accountId: 1,
  onEditField: jest.fn(() => jest.fn()),
};

const renderWithIntl = (ui: React.ReactElement) =>
  render(
    <IntlProvider locale="en" messages={enMessages}>
      {ui}
    </IntlProvider>,
  );

describe('KickoffEdit', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders MergedOutputList and passes fields and fieldsets', () => {
    const kickoff = {
      description: '',
      fields: [makeField('f1', 1)],
      fieldsets: [],
    };
    const fieldsets = [
      { id: 1, apiName: 'fs-1', name: 'FS', description: '', fields: [], order: 2 },
    ];

    renderWithIntl(
      <EditKickoff
        {...baseProps}
        kickoff={kickoff}
        fieldsets={fieldsets}
        onEditFieldsetField={jest.fn(() => jest.fn())}
      />,
    );

    expect(screen.queryByTestId('merged-output-list')).not.toBeNull();

    expect(MergedOutputList).toHaveBeenCalledWith(
      expect.objectContaining({
        fields: expect.arrayContaining([expect.objectContaining({ apiName: 'f1' })]),
        fieldsets,
      }),
      expect.anything(),
    );
  });

  it('passes empty fieldsets when none provided', () => {
    const kickoff = {
      description: '',
      fields: [makeField('f1', 0), makeField('f2', 1)],
      fieldsets: [],
    };

    renderWithIntl(<EditKickoff {...baseProps} kickoff={kickoff} />);

    expect(screen.queryByTestId('merged-output-list')).not.toBeNull();

    expect(MergedOutputList).toHaveBeenCalledWith(
      expect.objectContaining({
        fields: expect.arrayContaining([
          expect.objectContaining({ apiName: 'f1' }),
          expect.objectContaining({ apiName: 'f2' }),
        ]),
        fieldsets: [],
      }),
      expect.anything(),
    );
  });
});
