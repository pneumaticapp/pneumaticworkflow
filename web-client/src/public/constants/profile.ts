import { envLanguageCode } from "./enviroment";
import { TDropdownOptionBase } from "../components/UI";

// The Russian language is present, but it should not be shown yet
export const LANGUAGE_OPTIONS: TDropdownOptionBase[] = [
  { label: 'user-info.locale.language.english', value: 'en' },
  (envLanguageCode === 'ru' && { label: 'user-info.locale.language.russia', value: 'ru' })
].filter(Boolean) as unknown as TDropdownOptionBase[];

export const TIMEZONE_OPTIONS: TDropdownOptionBase[] = [
  { label: 'user-info.locale.timezone.baker-island', value: 'Etc/GMT+12'},
  { label: 'user-info.locale.timezone.pago-pago', value: 'US/Samoa'},
  { label: 'user-info.locale.timezone.hawaii', value: 'Pacific/Honolulu'},
  { label: 'user-info.locale.timezone.alaska', value: 'America/Anchorage'},
  { label: 'user-info.locale.timezone.los-angeles', value: 'America/Los_Angeles' },
  { label: 'user-info.locale.timezone.denver', value: 'America/Denver'},
  { label: 'user-info.locale.timezone.chicago', value: 'America/Chicago'},
  { label: 'user-info.locale.timezone.new-york', value: 'America/New_York'},
  { label: 'user-info.locale.timezone.caracas', value: 'America/Caracas'},
  { label: 'user-info.locale.timezone.buenos-aires', value: 'America/Buenos_Aires'},
  { label: 'user-info.locale.timezone.south-georgia', value: 'Atlantic/South_Georgia'},
  { label: 'user-info.locale.timezone.azores', value: 'Atlantic/Azores'},
  { label: 'user-info.locale.timezone.london', value: 'UTC'},
  { label: 'user-info.locale.timezone.berlin', value: 'Europe/Berlin'},
  { label: 'user-info.locale.timezone.cairo', value: 'Africa/Cairo'},
  { label: 'user-info.locale.timezone.moscow', value: 'Europe/Moscow'},
  { label: 'user-info.locale.timezone.dubai', value: 'Asia/Dubai'},
  { label: 'user-info.locale.timezone.karachi', value: 'Asia/Karachi'},
  { label: 'user-info.locale.timezone.dhaka', value: 'Asia/Dhaka'},
  { label: 'user-info.locale.timezone.bangkok', value: 'Asia/Bangkok'},
  { label: 'user-info.locale.timezone.beijing', value: 'Asia/Shanghai'},
  { label: 'user-info.locale.timezone.tokyo', value: 'Asia/Tokyo'},
  { label: 'user-info.locale.timezone.sydney', value: 'Australia/Sydney' },
  { label: 'user-info.locale.timezone.honiara', value: 'Pacific/Guadalcanal' },
  { label: 'user-info.locale.timezone.auckland', value: 'Pacific/Fiji' }
];

export const FIRST_DAY_OPTIONS: TDropdownOptionBase[] = [
  { label: 'user-info.locale.dateFdw.sunday', value: '0' },
  { label: 'user-info.locale.dateFdw.monday', value: '1' }
];

export const TIMEFORMAT_OPTIONS: TDropdownOptionBase[] = [
  { label: 'user-info.locale.timeformat.12', value: 'p' },
  { label: 'user-info.locale.timeformat.24', value: 'HH:mm' }
];

export const DATEFORMAT_OPTIONS: TDropdownOptionBase[] = [
  { label: 'user-info.locale.dateformat.month', value: 'MMM dd, yyy,' },
  { label: 'user-info.locale.dateformat.day', value: 'dd MMM, yyy,' }
];

export const TIMEZONE_OFFSET_MAP: any = {
  '-720': 'Etc/GMT+12',
  '-660': 'US/Samoa',
  '-600': 'Pacific/Honolulu',
  '-540': 'America/Anchorage',
  '-480': 'America/Los_Angeles',
  '-420': 'America/Denver',
  '-360': 'America/Chicago',
  '-300': 'America/New_York',
  '-240': 'America/Caracas',
  '-180': 'America/Buenos_Aires',
  '-120': 'Atlantic/South_Georgia',
  '-60': 'Atlantic/Azores',
  '0': 'UTC',
  '60': 'Europe/Berlin',
  '120': 'Africa/Cairo',
  '180': 'Europe/Moscow',
  '240': 'Asia/Dubai',
  '300': 'Asia/Karachi',
  '360': 'Asia/Dhaka',
  '420': 'Asia/Bangkok',
  '480': 'Asia/Shanghai',
  '540': 'Asia/Tokyo',
  '600': 'Australia/Sydney',
  '660': 'Pacific/Guadalcanal',
  '720': 'Pacific/Fiji',
};
