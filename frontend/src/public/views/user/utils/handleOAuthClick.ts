import type { MouseEvent } from 'react';
import type { IntlShape } from 'react-intl';

import type { EOAuthType } from '../../../types/auth';
import { getOAuthUrl } from '../../../api/getGoogleAuthUrl';
import { NotificationManager } from '../../../components/UI/Notifications';
import { isValidUri } from '../../../utils/urls';

export const handleOAuthClick =
  (type: EOAuthType, formatMessage: IntlShape['formatMessage']) => async (event: MouseEvent) => {
    event.preventDefault();

    const showServiceUnavailable = () => {
      NotificationManager.warning({
        message: formatMessage({ id: 'user.oauth-unavailable' }, { type }),
      });
    };

    try {
      const result = await getOAuthUrl(type);

      if (
        result &&
        typeof result === 'object' &&
        typeof result.redirectUri === 'string' &&
        isValidUri(result.redirectUri)
      ) {
        window.location.assign(result.redirectUri);
        return;
      }

      showServiceUnavailable();
    } catch {
      showServiceUnavailable();
    }
  };
