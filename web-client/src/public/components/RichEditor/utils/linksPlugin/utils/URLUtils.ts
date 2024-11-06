/* eslint-disable */
/* prettier-ignore */
import { prependHttp } from '../../../../../utils/prependHttp';
import { urlRegex } from './urlRegex';
import { mailRegex } from './mailRegex';

// tslint:disable-next-line: no-default-export
export default {
  isUrl(text: string): boolean {
    return urlRegex().test(text);
  },

  isMail(text: string): boolean {
    return mailRegex().test(text);
  },

  normaliseMail(email: string): string {
    if (email.toLowerCase().startsWith('mailto:')) {
      return email;
    }

    return `mailto:${email}`;
  },

  normalizeUrl(url: string): string {
    return prependHttp(url);
  },
};
