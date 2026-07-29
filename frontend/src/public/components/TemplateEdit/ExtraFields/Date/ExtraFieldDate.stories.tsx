import type { Meta, StoryObj } from '@storybook/react';
import { createIntl } from 'react-intl';

import { ExtraFieldDate } from './ExtraFieldDate';
import { EExtraFieldMode, EExtraFieldType, IExtraField } from '../../../../types/template';
import { EFieldLabelPosition } from '../../../../types/fieldset';
import { IWorkflowExtraFieldProps } from '../types';
import { enMessages } from '../../../../lang/locales/en_US';

const intl = createIntl({ locale: 'en-US', defaultLocale: 'en-US', messages: enMessages });

const editField = (updates: Partial<IExtraField>): void => {
  console.log('Field updated:', updates);
};

const defaultField: IExtraField = {
  apiName: 'date-field',
  name: 'Due Date',
  type: EExtraFieldType.Date,
  order: 0,
  userId: null,
  groupId: null,
  description: 'Select a due date',
  isRequired: false,
  isHidden: false,
  value: '',
  selections: [],
  attachments: [],
  dataset: null,
};

const meta: Meta<IWorkflowExtraFieldProps> = {
  title: 'UI/ExtraFieldDate',
  component: ExtraFieldDate,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    field: defaultField,
    intl,
    mode: EExtraFieldMode.Kickoff,
    editField,
    isDisabled: false,
    accountId: 1,
    labelPosition: EFieldLabelPosition.Top,
  },
};

export const Required: Story = {
  args: {
    field: { ...defaultField, value: '2024-01-01', isRequired: true },
    intl,
    mode: EExtraFieldMode.Kickoff,
    editField,
    isDisabled: false,
    accountId: 1,
    labelPosition: EFieldLabelPosition.Top,
  },
};

export const Disabled: Story = {
  args: {
    field: { ...defaultField, value: '2024-01-01' },
    intl,
    mode: EExtraFieldMode.Kickoff,
    editField,
    isDisabled: true,
    accountId: 1,
    labelPosition: EFieldLabelPosition.Top,
  },
};
