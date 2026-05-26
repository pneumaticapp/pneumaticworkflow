import { Request } from 'express';
import { GUEST_URLS, FORMS_PATH_PREFIX } from './constants';
import { EAppPart } from './types';

import { getConfig } from '../getConfig';

export const identifyAppPartOnServer = (req: Request): EAppPart => {
  const { formSubdomain } = getConfig();

  const identifyAppPartMap = [
    {
      // Path-based forms: domain.com/forms/*
      check: () => req.baseUrl === FORMS_PATH_PREFIX || req.path.startsWith(`${FORMS_PATH_PREFIX}/`),
      appPart: EAppPart.PublicFormApp,
    },
    {
      // Subdomain forms: form.domain.com/* (FORM_DOMAIN)
      check: () => !!formSubdomain && req.hostname.includes(formSubdomain),
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
