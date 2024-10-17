import { createIntl } from 'react-intl';
import { enMessages } from '../lang/locales/en_US';

const defaultLocale = 'en-US';
const locale = defaultLocale;
const messages = enMessages;

export const intlMock = createIntl({ locale, defaultLocale, messages });
