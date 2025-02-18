import type { Meta, StoryObj } from '@storybook/react';

import { TemplateSettings } from './TemplateSettings';

const meta: Meta<typeof TemplateSettings> = {
  component: TemplateSettings,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof TemplateSettings>;

export const workflowStarted: Story = {
  args: {},
};
