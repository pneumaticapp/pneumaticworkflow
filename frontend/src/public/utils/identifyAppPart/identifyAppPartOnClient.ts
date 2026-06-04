import { GUEST_URLS, isFormPath } from './constants';
import { EAppPart } from './types';

import { getBrowserConfig } from '../getConfig';
import { history } from '../history';

export const identifyAppPartOnClient = (): EAppPart => {
  const { config: { formSubdomain } } = getBrowserConfig();

  const identifyAppPartMap = [
    {
      // Forms: path-based (domain.com/forms/*) or subdomain (form.domain.com/*)
      check: () => isFormPath(
        window.location.hostname,
        window.location.pathname,
        formSubdomain,
      ),
      appPart: EAppPart.PublicFormApp,
    },
    {
      check: () => GUEST_URLS.some(url => history.location.pathname.includes(url)),
      appPart: EAppPart.GuestTaskApp,
    },
    {
      check: () => true,
      appPart: EAppPart.MainApp,
    },
  ];

  const appPart = identifyAppPartMap.find(({ check }) => check())?.appPart || EAppPart.MainApp;

  return appPart;
};
