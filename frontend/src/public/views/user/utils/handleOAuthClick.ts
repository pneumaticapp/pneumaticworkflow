import { MouseEvent } from 'react';
import { IntlShape } from 'react-intl';

import { EOAuthType } from '../../../types/auth';
import { getOAuthUrl } from '../../../api/getGoogleAuthUrl';
import { NotificationManager } from '../../../components/UI/Notifications';
import { httpProtocolRegex } from '../../../constants/defaultValues';

export const handleOAuthClick =
  (type: EOAuthType, formatMessage: IntlShape['formatMessage']) => async (event: MouseEvent) => {
    event.preventDefault();
    const service = type.startsWith('SSO') ? 'SSO' : type;

    const result = await getOAuthUrl(type);
    const isValidRedirect =
      result &&
      typeof result === 'object' &&
      typeof result.redirectUri === 'string' &&
      httpProtocolRegex.test(result.redirectUri);

    if (isValidRedirect) {
      window.location.assign(result.redirectUri);
      return;
    }

    NotificationManager.warning({
      message: formatMessage({ id: 'user.oauth-unavailable' }, { type: service }),
    });
  };
