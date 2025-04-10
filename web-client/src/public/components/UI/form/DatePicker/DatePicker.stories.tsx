import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { userEvent, within, expect } from '@storybook/test';
import { action } from "@storybook/addon-actions";
import { useState } from 'react';
import { DatePickerCustom } from './DatePicker';

const meta = {
  title: 'UI/DatePicker',
  component: DatePickerCustom,
  tags: ['autodocs'],
} satisfies Meta<typeof DatePickerCustom>;

export default meta;
type Story = StoryObj<typeof meta>;

// Создаем обертку с состоянием
const DatePickerWithState = () => {
  const [selectedDate, setSelectedDate] = useState<Date | null>(new Date('1993-02-23'));

  return (
    <DatePickerCustom
      selected={selectedDate}
      onChange={(date) => {
        setSelectedDate(date);
        action("date-changed")(date);
      }}
      startDay={true}
    />
  );
};

export const Default: Story = {
  args: {
    startDay: true,
    onChange: (date: Date | null) => console.log('Selected date:', date),
  },
  render: () => <DatePickerWithState />,
  play: async ({ canvasElement, step }) => {
    const canvas = within(canvasElement);

    await step('Open date picker', async () => {
      const input = canvas.getByRole('textbox');
      await userEvent.click(input);
    });

    await step('Verify month navigation', async () => {
      const nextMonthButton = canvas.getByRole('button', { name: /next month/i });
      const prevMonthButton = canvas.getByRole('button', { name: /previous month/i });

      const initialMonth = canvas.getByText(/February/, { selector: '.react-datepicker__current-month' });
      expect(initialMonth).toBeInTheDocument();

      await userEvent.click(nextMonthButton);
      const nextMonth = canvas.getByText(/March/, { selector: '.react-datepicker__current-month' });
      expect(nextMonth).toBeInTheDocument();

      await userEvent.click(prevMonthButton);
      await userEvent.click(prevMonthButton);
      const prevMonth = canvas.getByText(/January/, { selector: '.react-datepicker__current-month' });
      expect(prevMonth).toBeInTheDocument();

      await userEvent.click(nextMonthButton);
      const initialBaseMonth = canvas.getByText(/February/, { selector: '.react-datepicker__current-month' });
      expect(initialBaseMonth).toBeInTheDocument();

    });

    await step('Verify save button is disabled', async () => {
      const saveButton = canvas.getByRole('button', { name: /save/i });

      expect(saveButton).toBeDisabled();
    });

    await step('Verify date button changes background color on click', async () => {
      const dateButton = canvas.getByText('15', { selector: '.react-datepicker__day' });
      const initialBackgroundColor = window.getComputedStyle(dateButton).backgroundColor;

      await userEvent.click(dateButton);

      const dateButtonWithClick = canvas.getByText('15', { selector: '.react-datepicker__day' });

      const newBackgroundColor = window.getComputedStyle(dateButtonWithClick).backgroundColor;
      expect(newBackgroundColor).not.toBe(initialBackgroundColor);

      expect(newBackgroundColor).toBe('rgb(254, 195, 54)');
    });

    await step('Select a date', async () => {
      const dateButton = canvas.getByText('23', { selector: '.react-datepicker__day' });
      await userEvent.click(dateButton);
    });

    await step('Verify save button is enabled after date selection', async () => {
      const saveButton = canvas.getByRole('button', { name: /save/i });
      expect(saveButton).toBeEnabled();
    });

    await step('Verify date can be removed', async () => {
      const removeButton = canvas.getByRole('button', { name: /remove/i });
      await userEvent.click(removeButton);

      const input = canvas.getByRole('textbox');
      expect(input).toHaveValue('');

      const datepicker = canvas.queryByRole('dialog');
      expect(datepicker).not.toBeInTheDocument();
    });

    await step('Verify input value changes after date selection', async () => {
      const input = canvas.getByRole('textbox');
      await userEvent.click(input);

      const dateButton = canvas.getByText('15', { selector: '.react-datepicker__day' });
      await userEvent.click(dateButton);

      const saveButton = canvas.getByRole('button', { name: /save/i });
      await userEvent.click(saveButton);

      expect(input).toHaveValue(expect.stringMatching(/02\/15\/\d{4}/));

      const datepicker = canvas.queryByRole('dialog');
      expect(datepicker).not.toBeInTheDocument();
    });

    await step('Verify datepicker closes when clicking outside', async () => {
      const input = canvas.getByRole('textbox');
      await userEvent.click(input);

      const datepicker = canvas.getByRole('dialog');
      expect(datepicker).toBeInTheDocument();

      await userEvent.click(document.body);

      expect(canvas.queryByRole('dialog')).not.toBeInTheDocument();
    });
  }
};



export const StartOfDay: Story = {
  args: {
    selected: new Date(),
    onChange: (date: Date | null) => console.log('Selected date:', date),
    startDay: true
  },
  play: async ({ canvasElement, step }) => {
    const canvas = within(canvasElement);

    await step('Open date picker', async () => {
      const input = canvas.getByRole('textbox');
      await userEvent.click(input);
    });

    await step('Select a date', async () => {
      const dateButton = canvas.getByText('20', { selector: '.react-datepicker__day' });
      await userEvent.click(dateButton);
    });

    await step('Verify datepicker closes', async () => {
      const saveButton = canvas.getByRole('button', { name: /save/i });
      await userEvent.click(saveButton);
    });
  }
};

export const WithoutInitialDate: Story = {
  args: {
    selected: null,
    onChange: (date: Date | null) => console.log('Selected date:', date),
    startDay: true
  },
  play: async ({ canvasElement, step }) => {
    const canvas = within(canvasElement);

    await step('Open date picker', async () => {
      const input = canvas.getByRole('textbox');
      await userEvent.click(input);
    });

    await step('Select a date', async () => {
      const dateButton = canvas.getByText('10', { selector: '.react-datepicker__day' });
      await userEvent.click(dateButton);
    });

    await step('Verify datepicker closes', async () => {
      const saveButton = canvas.getByRole('button', { name: /save/i });
      await userEvent.click(saveButton);
    });

    await step('Open date picker', async () => {
      const input = canvas.getByRole('textbox');
      await userEvent.click(input);
    });


    await step('Clear the date', async () => {
      const input = canvas.getByRole('textbox');
      await userEvent.clear(input);
    });
  }
};
