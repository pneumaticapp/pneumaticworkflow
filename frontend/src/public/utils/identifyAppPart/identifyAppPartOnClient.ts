import { GUEST_URLS, getFormsBasename } from './constants';
import { EAppPart } from './types';

import { getBrowserConfig } from '../getConfig';
import { history } from '../history';

export const identifyAppPartOnClient = (): EAppPart => {
  const { config: { formSubdomain } } = getBrowserConfig();

  const identifyAppPartMap = [
    {
      // Path-based forms: domain.com/forms/*
      check: () => !!getFormsBasename(window.location.pathname),
      appPart: EAppPart.PublicFormApp,
    },
    {
      // Subdomain forms: form.domain.com/* (FORM_DOMAIN)
      check: () => !!formSubdomain
        && window.location.hostname.includes(formSubdomain),
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
