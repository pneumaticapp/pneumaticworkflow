import moment from 'moment-timezone';

export const setTimeForDate = (initialDate: Date, timeString: string, timezone: string, dateFmt: string): string => {
  const timeRegex12 = /(\d{1,2})(?::(\d{2}))?\s*?(am|pm)/;
  const timeRegex24 = /^([01][0-9]|2[0-3]):([0-5][0-9])$/;
  const match = dateFmt.split(', ')[2] === 'p' ? timeRegex12.exec(timeString) : timeRegex24.exec(timeString);
  if (!match) throw new Error('Invalid time');

  const [, hours, minutes = '00', period] = match;

  return moment(initialDate)
    .tz(timezone)
    .set({ h: period && period === 'pm' ? +hours + 12 : +hours, m: +minutes })
    .format();
};