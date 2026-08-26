import * as React from 'react';
import type { Meta, StoryObj } from '@storybook/react';

import { EConditionLogicOperations, EConditionOperators } from '../../../TaskForm/Conditions';
import { ConditionEdgeInfo, IConditionEdgeInfoProps } from './ConditionEdgeInfo';

const meta: Meta<IConditionEdgeInfoProps> = {
  title: 'TemplateEdit/ConditionEdgeInfo',
  component: ConditionEdgeInfo,
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <div style={{ display: 'flex', justifyContent: 'center', paddingTop: '12rem' }}>
        <Story />
      </div>
    ),
  ],
};

export default meta;
type Story = StoryObj<IConditionEdgeInfoProps>;

export const StartAfter: Story = {
  args: {
    startAfter: ['Prepare layout'],
  },
};

export const Conditional: Story = {
  args: {
    isConditional: true,
    summary: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Quisque facilisis odio eu diam efficitur malesuada',
  },
};

export const Clause: Story = {
  args: {
    isConditional: true,
    clauses: [
      {
        fieldLabel: 'Client',
        operator: EConditionOperators.Exist,
        logicOperation: EConditionLogicOperations.And,
      },
    ],
  },
};
