import { Request } from 'express';
import { GUEST_URLS } from './constants';
import { EAppPart } from './types';

import { getConfig } from '../getConfig';

export const identifyAppPartOnServer = (req: Request): EAppPart => {
  const identifyAppPartMap = [
    {
      check: () => {
        const { formSubdomain } = getConfig();

        return req.hostname.includes(formSubdomain);
      },
      appPart: EAppPart.PublicFormApp,
    },
    {
      check: () => GUEST_URLS.some(url => req.url.includes(url)),
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
