import { MouseEvent } from 'react';
import { IntlShape } from 'react-intl';

import { EOAuthType } from '../../../types/auth';
import { getOAuthUrl } from '../../../api/getGoogleAuthUrl';
import { NotificationManager } from '../../../components/UI/Notifications';

const ALLOWED_PROTOCOLS = new Set(['http:', 'https:']);

const isValidUri = (value: string) => {
  try {
    const { protocol } = new URL(value);
    return ALLOWED_PROTOCOLS.has(protocol);
  } catch {
    return false;
  }
};

export const handleOAuthClick =
  (type: EOAuthType, formatMessage: IntlShape['formatMessage']) => async (event: MouseEvent) => {
    event.preventDefault();

    const showServiceUnavailable = () => {
      const service =
        type === EOAuthType.SSOAuth0 || type === EOAuthType.SSOOkta
          ? formatMessage({ id: 'user.oauth-unavailable-sso' })
          : type;

      NotificationManager.warning({
        message: formatMessage({ id: 'user.oauth-unavailable' }, { type: service }),
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
