/* eslint-disable import/prefer-default-export */
/* eslint-disable prefer-template */
/* eslint-disable prefer-rest-params */
/* eslint-disable vars-on-top */
/* eslint-disable func-names */
/* eslint-disable no-var */
// @ts-nocheck

import { TAuthUserResult } from '../redux/actions';
import { getBrowserConfig } from './getConfig';
import { getUserFullName } from './users';

const PROD_APP_ID = 'y8ocj31v';
const DEV_APP_ID = 'jsyjlrnf';

export function setIntercomUser(user: TAuthUserResult) {
  const { env = 'local' } = getBrowserConfig();

  const appIdMap = {
    local: DEV_APP_ID,
    staging: DEV_APP_ID,
    prod: PROD_APP_ID,
  };

  const APP_ID = appIdMap[env];

  window.intercomSettings = {
    app_id: APP_ID,
    name: getUserFullName(user),
    email: user.email,
    user_id: String(user.id),
  };

  // Intercom reinitializing
  (function () {
    var w = window;
    var ic = w.Intercom;
    if (typeof ic === 'function') {
      ic('reattach_activator');
      ic('update', w.intercomSettings);
    } else {
      var d = document;
      var i = function () {
        i.c(arguments);
      };
      i.q = [];
      i.c = function (args) {
        i.q.push(args);
      };
      w.Intercom = i;
      var l = function () {
        var s = d.createElement('script');
        s.type = 'text/javascript';
        s.async = true;
        s.src = 'https://widget.intercom.io/widget/' + APP_ID;
        var x = d.getElementsByTagName('script')[0];
        x.parentNode.insertBefore(s, x);
      };
      if (document.readyState === 'complete') {
        l();
      } else if (w.attachEvent) {
        w.attachEvent('onload', l);
      } else {
        w.addEventListener('load', l, false);
      }
    }
  })();
}
