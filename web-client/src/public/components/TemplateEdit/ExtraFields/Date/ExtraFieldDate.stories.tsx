import type { Meta, StoryObj } from '@storybook/react';
import { ExtraFieldDate } from './ExtraFieldDate';
import { EExtraFieldMode } from '../../../../types/template';

const meta = {
  title: 'UI/ExtraFieldDate',
  component: ExtraFieldDate as React.ComponentType<any>,
  tags: ['autodocs'],
} satisfies Meta<typeof ExtraFieldDate>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    field: {
      value: null,
      name: 'Due Date',
      isRequired: false,
      description: 'Select a due date'
    },
    intl: {
      formatMessage: ({ id }) => id
    },
    mode: EExtraFieldMode.Kickoff,
    editField: (updates) => console.log('Field updated:', updates),
    isDisabled: false
  }
};

export const Required: Story = {
  args: {
    field: {
      value: '2024-01-01',
      name: 'Due Date',
      isRequired: true,
      description: 'Select a due date'
    },
    intl: {
      formatMessage: ({ id }) => id
    },
    mode: EExtraFieldMode.Kickoff,
    editField: (updates) => console.log('Field updated:', updates),
    isDisabled: false
  }
};

export const Disabled: Story = {
  args: {
    field: {
      value: '2024-01-01',
      name: 'Due Date',
      isRequired: false,
      description: 'Select a due date'
    },
    intl: {
      formatMessage: ({ id }) => id
    },
    mode: EExtraFieldMode.Kickoff,
    editField: (updates) => console.log('Field updated:', updates),
    isDisabled: true
  }
};
