import type { Meta, StoryObj } from '@storybook/react';

import { WebhookItem } from './WebhooksItem';
import { EWebhooksSubscriberStatus, EWebhooksTypeEvent } from '../../../../types/webhooks';

const meta: Meta<typeof WebhookItem> = {
  component: WebhookItem,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof WebhookItem>;

export const workflowStarted: Story = {
  args: {
    url: '',
    status: EWebhooksSubscriberStatus.NotSubscribed,
    event: EWebhooksTypeEvent.workflowStarted,
  },
};

export const workflowCompleted: Story = {
  args: {
    url: '',
    status: EWebhooksSubscriberStatus.NotSubscribed,
    event: EWebhooksTypeEvent.workflowCompleted,
  },
};

export const taskCompleted: Story = {
  args: {
    url: '',
    status: EWebhooksSubscriberStatus.NotSubscribed,
    event: EWebhooksTypeEvent.taskCompleted,
  },
};

export const taskReturned: Story = {
  args: {
    url: '',
    status: EWebhooksSubscriberStatus.NotSubscribed,
    event: EWebhooksTypeEvent.taskReturned,
  },
};

export const Unknown: Story = {
  args: {
    url: 'https://example.com',
    status: EWebhooksSubscriberStatus.Unknown,
    event: EWebhooksTypeEvent.taskCompleted,
  },
};

export const NotSubscribed: Story = {
  args: {
    url: 'https://example.com',
    status: EWebhooksSubscriberStatus.NotSubscribed,
    event: EWebhooksTypeEvent.taskCompleted,
  },
};

export const Subscribed: Story = {
  args: {
    url: 'https://example.com',
    status: EWebhooksSubscriberStatus.Subscribed,
    event: EWebhooksTypeEvent.taskCompleted,
  },
};

export const Loading: Story = {
  args: {
    url: 'https://example.com',
    status: EWebhooksSubscriberStatus.Loading,
    event: EWebhooksTypeEvent.taskCompleted,
  },
};

export const Subscribing: Story = {
  args: {
    url: 'https://example.com',
    status: EWebhooksSubscriberStatus.Subscribing,
    event: EWebhooksTypeEvent.taskCompleted,
  },
};

export const Unsubscribing: Story = {
  args: {
    url: 'https://example.com',
    status: EWebhooksSubscriberStatus.Unsubscribing,
    event: EWebhooksTypeEvent.taskCompleted,
  },
};
