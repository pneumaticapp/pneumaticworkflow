import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { IntlProvider } from 'react-intl';

import { RangeDatePicker } from '../components/RangeDatePicker/RangeDatePicker';
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

const renderRangeDatePicker = (props: Partial<React.ComponentProps<typeof RangeDatePicker>> = {}) => {
  const defaultProps: React.ComponentProps<typeof RangeDatePicker> = {
    selectsRange: true,
    startDate: new Date('2024-06-10T00:00:00.000Z'),
    endDate: new Date('2024-06-20T00:00:00.000Z'),
    onChange: jest.fn(),
    ...props,
  };

  return render(
    <IntlProvider locale="en" messages={enMessages as unknown as Record<string, string>}>
      <RangeDatePicker {...defaultProps} />
    </IntlProvider>,
  );
};

describe('RangeDatePicker', () => {
  it('clears the selected range without crashing when clear returns null', async () => {
    const onChange = jest.fn();

    renderRangeDatePicker({ onChange });

    const clearButton = screen.getByLabelText(/clear/i);
    userEvent.click(clearButton);

    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith([null, null]);
    });
  });
});
