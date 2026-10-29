import moment from 'moment-timezone';

export const toEndOfDay = (date: moment.Moment): moment.Moment =>
  date.clone().set({ hour: 23, minute: 59, second: 59, millisecond: 0 });
