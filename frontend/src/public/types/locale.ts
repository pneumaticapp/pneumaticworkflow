export const enum ELocale {
  English = 'en',
  Russian = 'ru',
}

export const enum ELocaleDirection {
  LeftToRight = 'ltr',
  RightToLeft = 'rtl',
}

export interface ILocaleOption {
  id: ELocale;
  name: string;
  direction: ELocaleDirection;
}
