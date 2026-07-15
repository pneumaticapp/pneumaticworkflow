import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { IntlProvider } from 'react-intl';

import { DateFilter } from '../DateFilter';
import { EHighlightsDateFilter } from '../../../types/highlights';
import { enMessages } from '../../../lang/locales/en_US';
import { ELocale } from '../../../types/redux';

jest.mock('react-redux', () => ({
  useSelector: (selector: (state: unknown) => unknown) =>
    selector({
      authUser: {
        timezone: 'UTC',
        language: ELocale.English,
        dateFdw: 0,
      },
    }),
}));

const renderDateFilter = (props: Partial<React.ComponentProps<typeof DateFilter>> = {}) => {
  const defaultProps: React.ComponentProps<typeof DateFilter> = {
    startDate: new Date('2024-06-10'),
    endDate: new Date('2024-06-20'),
    selectedDateFilter: EHighlightsDateFilter.Custom,
    changeEndDate: jest.fn(),
    changeStartDate: jest.fn(),
    changeSelectedDateFilter: () => jest.fn(),
    ...props,
  };

  return render(
    <IntlProvider locale="en" messages={enMessages as unknown as Record<string, string>}>
      <DateFilter {...defaultProps} />
    </IntlProvider>,
  );
};

describe('DateFilter', () => {
  it('renders a single range datepicker for Custom filter', () => {
    renderDateFilter();

    expect(screen.getByRole('textbox')).toBeInTheDocument();
    expect(screen.getAllByRole('textbox')).toHaveLength(1);
  });

  it('does not render Save button in custom range picker', () => {
    renderDateFilter();

    userEvent.click(screen.getByRole('textbox'));

    expect(screen.queryByRole('button', { name: /save/i })).not.toBeInTheDocument();
  });
});
