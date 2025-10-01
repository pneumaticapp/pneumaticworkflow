import moment from 'moment-timezone';

export const checkMinTimeForDate = (dateWithTime: string, timezone: string): boolean => {
  const selectedDateTime = moment(dateWithTime).tz(timezone);
  const minAllowedTime = moment.tz(timezone).add(1, 'minute');

  return selectedDateTime.isAfter(minAllowedTime);
};