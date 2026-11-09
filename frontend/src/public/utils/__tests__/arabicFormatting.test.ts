import moment from 'moment';
import '../../lang/momentLocale';
import {
  formatDateToQuery,
  formatDelayRequest,
  formatDuration,
  formatDurationMonths,
  toISOStringFromTsp,
  toDateString,
  toTspDate,
  getEndOfDayTsp,
} from '../dateTime';
import { getTime } from '../strings';
import { setTimeForDate } from '../../components/DueIn/utils/setTimeForDate';

describe('Arabic display and machine-readable date values', () => {
  const originalLocale = moment.locale();
  beforeEach(() => moment.locale('ar-sy'));
  afterEach(() => moment.locale(originalLocale));

  it('keeps API date and duration values in ASCII', () => {
    expect(decodeURIComponent(formatDateToQuery(new Date('2026-11-09T10:00:00Z'))!)).toMatch(/^[\dT:-]+$/);
    expect(toISOStringFromTsp(0)).toBe('1970-01-01T00:00:00Z');
    expect(formatDelayRequest({ days: 1, hours: 2, minutes: 30 })).toBe('01 02:30:00');
  });

  it('round-trips the editable time under an Arabic global locale', () => {
    const date = '2026-11-09T10:00:00Z';
    const value = getTime(date, 'UTC', 'MMM dd, yyy, p');
    expect(value).toBe('10:00am');
    expect(setTimeForDate(new Date(date), value, 'UTC', 'MMM dd, yyy, p')).toBe('2026-11-09T10:00:00Z');
  });

  it('localizes visible durations only', () => {
    expect(formatDurationMonths(1)).toBe('شهر');
    expect(formatDurationMonths(2)).toBe('شهران');
    expect(formatDurationMonths(3)).toContain('أشهر');
    expect(formatDurationMonths(100)).toBe('١٠٠ شهر');
    expect(formatDuration('1 02:30:00', 'D[d] H[h] m[m]')).not.toMatch(/[dhm]/);
  });

  it('round-trips an Arabic display date after switching the UI back to English', () => {
    const timestamp = Date.UTC(2026, 0, 5) / 1000;
    const arabicDate = toDateString(timestamp, 'UTC')!;
    expect(arabicDate).toContain('كانون الثاني');
    moment.locale('en');
    const reparsed = toTspDate(arabicDate)!;
    expect(moment.unix(reparsed).format('YYYY-MM-DD')).toBe('2026-01-05');
    expect(moment.unix(getEndOfDayTsp(arabicDate)!).format('YYYY-MM-DD')).toBe('2026-01-05');
    expect(toDateString(arabicDate, 'UTC')).not.toBeNull();
  });
});
