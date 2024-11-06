import { IntlShape } from "react-intl";
import moment from 'moment-timezone';
import { useSelector } from "react-redux";
import { getLanguage } from "../../../redux/selectors/user";

type TSnoozeOption = {
  title: string;
  dateString: string;
  dateISOString: string;
};

export function getSnoozeOptions(formatMessage: IntlShape['formatMessage'], timezone: string): TSnoozeOption[] {
  const today = moment.tz(timezone);

  const currentLocale = useSelector(getLanguage)
  moment.locale(currentLocale);

  const snoozeSettings = [
    {
      title: formatMessage({ id: 'snooze.day' }),
      calcDate: () => today.add(1, 'day'),
    },
    {
      title: formatMessage({ id: 'snooze.week' }),
      calcDate: () => today.add(1, 'week'),
    },
    {
      title: formatMessage({ id: 'snooze.month' }),
      calcDate: () => today.add(1, 'month'),
    },
  ];

  const snoozeOptions: TSnoozeOption[] = snoozeSettings.map(({ title, calcDate }) => {
    const date = calcDate();

    return {
      title,
      dateString: date.format('MMMM d'),
      dateISOString: date.format(),
    };
  });

  return snoozeOptions;
}
