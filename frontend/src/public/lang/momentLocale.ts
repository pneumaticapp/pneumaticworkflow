import moment from 'moment';
import { syrianMonths } from './dateLocale';

// Moment has Arabic locales but no ar-sy in the installed version.
const previousLocale = moment.locale();
// Registration modules change Moment's global locale. Load them only after
// capturing it, rather than letting static imports silently select Russian.
require('moment/locale/ar');
require('moment/locale/ru');
moment.defineLocale('ar-sy', {
  parentLocale: 'ar',
  months: syrianMonths,
  monthsShort: syrianMonths,
  week: { dow: 0, doy: 6 },
});
moment.locale(previousLocale);
