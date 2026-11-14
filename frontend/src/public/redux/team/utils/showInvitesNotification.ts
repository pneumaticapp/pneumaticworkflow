import type { InviteResponse } from '../../../api/sendInvites';
import { NotificationManager } from '../../../components/UI/Notifications';
import { getPluralNoun } from '../../../utils/helpers';
import type { IUserInvitePayload } from '../../../types/team';

export interface IShowNotification {
  (type: 'success' | 'warning', invites: IUserInvitePayload[], title?: string): void;
}

export interface IShowInvitesNotification {
  invites: IUserInvitePayload[];
  sendInvitesResult: InviteResponse;
}

export const showInvitesNotification = ({ invites, sendInvitesResult }: IShowInvitesNotification) => {
  const showNotification: IShowNotification = (type, invites, title) => {
    if (!invites.length) {
      return;
    }
    const notification = type === 'success' ? NotificationManager.success : NotificationManager.warning;
    const preNotificationTitle = type === 'success' ? 'Successfully invited' : 'Failed to invite';
    notification({
      title:
        title ||
        `${preNotificationTitle} ${getPluralNoun({
          counter: invites.length,
          single: 'user',
          plural: 'users',
          includeCounter: true,
        })}`,
      message: invites.map(({ email }) => email).join('\n'),
    });
  };

  const { alreadyAccepted } = sendInvitesResult;
  const alreadyAcceptedEmails = alreadyAccepted.map(({ email }) => email);
  const alreadyAcceptedUsers = invites.filter(({ email }) => alreadyAcceptedEmails.includes(email));
  const successfullyInvitedUsers = invites.filter(({ email }) => !alreadyAcceptedEmails.includes(email));

  showNotification('warning', alreadyAcceptedUsers, 'users.error-already-accepted');
  showNotification('success', successfullyInvitedUsers);
};
