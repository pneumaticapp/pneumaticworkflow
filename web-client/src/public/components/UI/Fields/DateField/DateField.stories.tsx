import type { Meta, StoryObj } from '@storybook/react';
import { DateField } from './DateField';

const meta = {
  title: 'UI/DateField',
  component: DateField,
  tags: ['autodocs'],
} satisfies Meta<typeof DateField>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    value: '2024-01-15',
    onChange: (date) => console.log('Date changed:', date),
    placeholder: 'Select a date'
  }
};

export const WithTitle: Story = {
  args: {
    ...Default.args,
    title: 'Date Field Title'
  }
};

export const WithError: Story = {
  args: {
    ...Default.args,
    errorMessage: 'Please select a valid date'
  }
};

export const Required: Story = {
  args: {
    ...Default.args,
    isRequired: true,
    title: 'Required Date Field'
  }
};

export const Disabled: Story = {
  args: {
    ...Default.args,
    disabled: true,
    title: 'Disabled Date Field'
  }
};

export const SmallSize: Story = {
  args: {
    ...Default.args,
    fieldSize: 'sm',
    title: 'Small Date Field'
  }
};

export const MediumSize: Story = {
  args: {
    ...Default.args,
    fieldSize: 'md',
    title: 'Medium Date Field'
  }
};

export const LargeSize: Story = {
  args: {
    ...Default.args,
    fieldSize: 'lg',
    title: 'Large Date Field'
  }
};
