import { Request } from 'express';
import { GUEST_URLS, FORMS_PATH_PREFIX, isFormPath } from './constants';
import { EAppPart } from './types';

import { getConfig } from '../getConfig';

export const identifyAppPartOnServer = (req: Request): EAppPart => {
  const { formSubdomain } = getConfig();

  const identifyAppPartMap = [
    {
      // Forms: path-based (domain.com/forms/*), subdomain (form.domain.com/*),
      // or Express-mounted sub-app at /forms
      check: () => req.baseUrl === FORMS_PATH_PREFIX
        || isFormPath(req.hostname, req.path, formSubdomain),
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
