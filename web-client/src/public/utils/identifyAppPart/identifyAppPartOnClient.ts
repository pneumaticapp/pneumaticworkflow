import { GUEST_URLS } from './constants';
import { EAppPart } from './types';

import { getBrowserConfig } from '../getConfig';
import { history } from '../history';

export const identifyAppPartOnClient = (): EAppPart => {
  const identifyAppPartMap = [
    {
      check: () => {
        const { config: { formSubdomain } } = getBrowserConfig();

        return window.location.hostname.includes(formSubdomain);
      },
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
