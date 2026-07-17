import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { IntlProvider } from 'react-intl';

import { SingleDatePicker } from '../components/SingleDatePicker/SingleDatePicker';
import { enMessages } from '../../../../../lang/locales/en_US';
import { ELocale } from '../../../../../types/redux';

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

const renderSingleDatePicker = (props: Partial<React.ComponentProps<typeof SingleDatePicker>> = {}) => {
  const defaultProps: React.ComponentProps<typeof SingleDatePicker> = {
    selected: new Date('2024-06-15T00:00:00.000Z'),
    onChange: jest.fn(),
    startDay: true,
    ...props,
  };

  return render(
    <IntlProvider locale="en" messages={enMessages as unknown as Record<string, string>}>
      <SingleDatePicker {...defaultProps} />
    </IntlProvider>,
  );
};

describe('SingleDatePicker', () => {
  it('clears the selected date via clear button', async () => {
    const onChange = jest.fn();

    renderSingleDatePicker({ onChange });

    const clearButton = screen.getByLabelText(/clear/i);
    userEvent.click(clearButton);

    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith(null);
    });
  });

  it('does not render built-in clear button when isClearable is false', () => {
    renderSingleDatePicker({ isClearable: false });

    expect(screen.queryByLabelText(/clear/i)).not.toBeInTheDocument();
  });

  it('does not render clear button when there is no selected date', () => {
    renderSingleDatePicker({ selected: null });

    expect(screen.queryByLabelText(/clear/i)).not.toBeInTheDocument();
  });
});
