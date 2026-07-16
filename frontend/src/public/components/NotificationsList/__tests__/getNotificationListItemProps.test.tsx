/// <reference types="jest" />
import { createIntl } from 'react-intl';

import { enMessages } from '../../../lang/locales/en_US';
import { TNotificationsListItem } from '../../../types';
import { getNotificationListItemProps } from '../getNotificationListItemProps';

jest.mock('../../UI/DateFormat/container', () => ({
  DateFormat: () => null,
}));

describe('getNotificationListItemProps', () => {
  it('maps a completed workflow notification to a workflow link', () => {
    const notification: TNotificationsListItem = {
      id: 1,
      status: 'new',
      datetime: '2026-07-16T12:00:00Z',
      type: 'complete_workflow',
      workflow: {
        id: 42,
        name: 'Onboarding',
      },
    };
    const { formatMessage } = createIntl({ locale: 'en', messages: enMessages });

    const props = getNotificationListItemProps({
      notification,
      users: [],
      formatMessage,
      removeNotificationItem: jest.fn(),
    });

    expect(props).toMatchObject({
      title: 'Pneumatic',
      subtitle: 'Onboarding',
      text: 'Workflow was completed',
      link: '/workflows/42/',
      status: 'new',
    });
    expect(props?.avatar).toBeTruthy();
    expect(props?.icon).toBeTruthy();
  });
});
