/* eslint-disable */
/* prettier-ignore */
/* tslint:disable:
no-any no-var-keyword only-arrow-functions newline-before-return curly prefer-template trailing-comma whitespace
*/

// This code snippet is original segment snippet
// The only difference is that window.analytics was type casted as any, added project logger
// And every tslint error was suppressed
// https://segment.com/docs/connections/sources/catalog/libraries/website/javascript/quickstart/

import { getAnalyticsId, getAnalyticsPageParams } from './utils';
import { logger } from '../logger';

export function loadAnalytics() {
  // Create a queue, but don't obliterate an existing one!
  let analytics = (window as any).analytics = (window as any).analytics || [];

  // If the real analytics.js is already on the page return.
  if (analytics.initialize) {
    return;
  }

  // If the snippet was invoked already show an error.
  if (analytics.invoked) {
    if (window.console) {
      logger.error('Segment snippet included twice.');
    }

    return;
  }

  // Invoked flag, to make sure the snippet
  // is never invoked twice.
  analytics.invoked = true;

  // A list of the methods in Analytics.js to stub.
  analytics.methods = [
    'trackSubmit',
    'trackClick',
    'trackLink',
    'trackForm',
    'pageview',
    'identify',
    'reset',
    'group',
    'track',
    'ready',
    'alias',
    'debug',
    'page',
    'once',
    'off',
    'on',
    'addSourceMiddleware',
    'addIntegrationMiddleware',
    'setAnonymousId',
    'addDestinationMiddleware',
  ];

  // Define a factory to create stubs. These are placeholders
  // for methods in Analytics.js so that you never have to wait
  // for it to load to actually record data. The `method` is
  // stored as the first argument, so we can replay the data.
  analytics.factory = function(method: any) {
    return function() {
      let args = Array.prototype.slice.call(arguments);
      args.unshift(method);
      analytics.push(args);

      return analytics;
    };
  };

  // For each of our methods, generate a queueing stub.
  for (let i = 0; i < analytics.methods.length; i++) {
    let key = analytics.methods[i];
    analytics[key] = analytics.factory(key);
  }

  // Define a method to load Analytics.js from our CDN,
  // and that will be sure to only ever load it once.
  analytics.load = function(key: any, options: any) {
    // Create an async script element based on your key.
    let script = document.createElement('script');
    script.type = 'text/javascript';
    script.async = true;
    script.src = `https://cdn.segment.com/analytics.js/v1/${
      key  }/analytics.min.js`;

    // Insert our script next to the first script element.
    let first = document.getElementsByTagName('script')[0];

    if (first && first.parentNode) {
      first.parentNode.insertBefore(script, first);
    }

    // first.parentNode.insertBefore(script, first);
    analytics._loadOptions = options;
  };

  // Add a version to keep track of what's in the wild.
  analytics.SNIPPET_VERSION = '4.1.0';

  // Load Analytics.js with your key, which will automatically
  // load the tools you've enabled for your account. Boosh!
  analytics.load(getAnalyticsId());

  // Make the first page call to load the integrations. If
  // you'd like to manually name or tag the page, edit or
  // move this call however you'd like.
  const { pathname, search } = document.location;
  analytics.page(...getAnalyticsPageParams(pathname, search));
}
