import type { Meta, StoryObj } from '@storybook/react';
import { ExtraFieldDate } from './ExtraFieldDate';
import { EExtraFieldMode, IExtraField } from '../../../../types/template';

const meta = {
  title: 'UI/ExtraFieldDate',
  component: ExtraFieldDate as React.ComponentType<unknown>,
  tags: ['autodocs'],
} satisfies Meta<typeof ExtraFieldDate>;

export default meta;
type Story = StoryObj<typeof meta>;

const formatMessage = ({ id }: { id: string }): string => id;
const editField = (updates: Partial<IExtraField>): void => {
  console.log('Field updated:', updates);
};

export const Default: Story = {
  args: {
    field: {
      value: null,
      name: 'Due Date',
      isRequired: false,
      description: 'Select a due date'
    },
    intl: {
      formatMessage
    },
    mode: EExtraFieldMode.Kickoff,
    editField,
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
      formatMessage
    },
    mode: EExtraFieldMode.Kickoff,
    editField,
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
      formatMessage
    },
    mode: EExtraFieldMode.Kickoff,
    editField,
    isDisabled: true
  }
};
