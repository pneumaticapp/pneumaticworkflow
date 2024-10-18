import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';
import { PlayLogoIcon } from '../../../icons';

const meta: Meta<typeof Button> = {
  component: Button,
};

export default meta;
type Story = StoryObj<typeof Button>;

export const Default: Story = {
  args: {
    wrapper: 'button',
    label: 'Save workflow',
    size: 'lg',
    buttonStyle: "yellow",
    icon: PlayLogoIcon
  },
};
