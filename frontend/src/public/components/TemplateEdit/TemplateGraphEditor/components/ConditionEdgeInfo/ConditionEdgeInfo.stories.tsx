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

export const Conditional: Story = {
  args: {
    summary: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Quisque facilisis odio eu diam efficitur malesuada',
  },
};

export const Clause: Story = {
  args: {
    clauses: [
      {
        fieldLabel: 'Client',
        operator: EConditionOperators.Exist,
        logicOperation: EConditionLogicOperations.And,
      },
    ],
  },
};
