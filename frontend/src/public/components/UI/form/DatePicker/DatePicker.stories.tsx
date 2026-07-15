import React, { useState } from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { userEvent, within, expect } from '@storybook/test';
import { action } from '@storybook/addon-actions';

import { DatePickerCustom } from './DatePicker';
import { IRangeDatePickerProps, ISingleDatePickerProps } from './types';

const meta = {
  title: 'UI/DatePicker',
  component: DatePickerCustom,
  tags: ['autodocs'],
} satisfies Meta<ISingleDatePickerProps>;

export default meta;

type TSingleStory = StoryObj<Meta<ISingleDatePickerProps>>;
type TRangeStory = StoryObj<Meta<IRangeDatePickerProps>>;

interface ISingleDatePickerStateProps extends Omit<ISingleDatePickerProps, 'onChange' | 'selected'> {
  initialDate?: Date | null;
}

const SingleDatePickerWithState = ({ initialDate = null, ...props }: ISingleDatePickerStateProps) => {
  const [selectedDate, setSelectedDate] = useState<Date | null>(initialDate);

  return (
    <DatePickerCustom
      {...props}
      selected={selectedDate}
      onChange={(date: Date | null) => {
        setSelectedDate(date);
        action('date-changed')(date);
      }}
    />
  );
};

interface IRangeDatePickerStateProps extends Omit<IRangeDatePickerProps, 'onChange' | 'startDate' | 'endDate' | 'selectsRange'> {
  initialStartDate?: Date | null;
  initialEndDate?: Date | null;
}

const RangeDatePickerWithState = ({
  initialStartDate = null,
  initialEndDate = null,
  ...props
}: IRangeDatePickerStateProps) => {
  const [startDate, setStartDate] = useState<Date | null>(initialStartDate);
  const [endDate, setEndDate] = useState<Date | null>(initialEndDate);

  return (
    <DatePickerCustom
      {...props}
      endDate={endDate}
      onChange={([start, end]: [Date | null, Date | null]) => {
        if (start) {
          setStartDate(start);
        }

        if (end) {
          setEndDate(end);
        }

        action('range-changed')([start, end]);
      }}
      selectsRange
      startDate={startDate}
    />
  );
};

export const Default: TSingleStory = {
  render: () => <SingleDatePickerWithState initialDate={new Date('1993-02-23')} startDay />,
  play: async ({ canvasElement, step }) => {
    const canvas = within(canvasElement);

    await step('Open date picker', async () => {
      const input = canvas.getByRole('textbox');
      await userEvent.click(input);
    });

    await step('Select a date and verify picker closes', async () => {
      const dateButton = canvas.getByText('23', { selector: '.react-datepicker__day' });
      await userEvent.click(dateButton);

      const input = canvas.getByRole('textbox');
      expect(input).toHaveValue(expect.stringMatching(/Feb 23, 1993/i));
      expect(canvas.queryByRole('dialog')).not.toBeInTheDocument();
    });
  },
};

export const StartOfDay: TSingleStory = {
  render: () => <SingleDatePickerWithState initialDate={new Date()} startDay />,
};

export const EndOfDay: TSingleStory = {
  render: () => <SingleDatePickerWithState initialDate={new Date('2024-06-15')} />,
};

export const Inline: TSingleStory = {
  render: () => <SingleDatePickerWithState initialDate={new Date('2024-06-15')} inline startDay />,
};

export const Range: TRangeStory = {
  render: () => <RangeDatePickerWithState placeholderText="Start date — End date" />,
  play: async ({ canvasElement, step }) => {
    const canvas = within(canvasElement);

    await step('Open date picker', async () => {
      const input = canvas.getByRole('textbox');
      await userEvent.click(input);
    });

    await step('Select start date', async () => {
      const startDateButton = canvas.getByText('10', { selector: '.react-datepicker__day' });
      await userEvent.click(startDateButton);

      expect(canvas.getByRole('dialog')).toBeInTheDocument();
    });

    await step('Select end date and verify picker closes', async () => {
      const endDateButton = canvas.getByText('20', { selector: '.react-datepicker__day' });
      await userEvent.click(endDateButton);

      expect(canvas.queryByRole('dialog')).not.toBeInTheDocument();
    });
  },
};

export const RangeWithInitialDates: TRangeStory = {
  render: () => (
    <RangeDatePickerWithState
      initialEndDate={new Date('2024-06-20')}
      initialStartDate={new Date('2024-06-10')}
      placeholderText="Start date — End date"
    />
  ),
};
