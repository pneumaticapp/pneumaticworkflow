import { GUEST_URLS } from './constants';
import { EAppPart } from './types';

import { getBrowserConfig } from '../getConfig';
import { history } from '../history';

export const identifyAppPartOnClient = (): EAppPart => {
  const hostname = window.location.hostname;
  const pathname = window.location.pathname;
  const href = window.location.href;
  
  // Check if this URL looks like a public form (starts with alphanumeric token)
  const isPublicFormUrl = /^\/[a-zA-Z0-9]{8,}$/.test(pathname);
  
  console.log('identifyAppPartOnClient debug:', {
    hostname,
    pathname,
    href,
    isPublicFormUrl
  });
  
  // Force forms to be recognized as PublicFormApp for form.localhost or public form URLs
  if (hostname === 'form.localhost' || isPublicFormUrl) {
    console.log('Forced PublicFormApp detection - hostname:', hostname, 'isPublicFormUrl:', isPublicFormUrl);
    return EAppPart.PublicFormApp;
  }
  
  const identifyAppPartMap = [
    {
      check: () => {
        const { config: { formSubdomain } } = getBrowserConfig();
        
        // Check if this is the forms subdomain or public form URL
        const isFormsSubdomain = formSubdomain && (hostname === formSubdomain || hostname.includes(formSubdomain));
        
        console.log('formSubdomain check:', {
          hostname,
          formSubdomain,
          isFormsSubdomain,
          isPublicFormUrl
        });
        
        return isFormsSubdomain || isPublicFormUrl;
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
  
  console.log('Final appPart:', appPart);
  return appPart;
};
