import type { IntlShape } from 'react-intl';

interface IEnumSelectOption<T extends string> {
  value: T;
  label: string;
}

export function getEnumSelectProps<T extends string>(
  values: T[],
  activeValue: T,
  onChange: (value: T) => void,
  formatMessage: IntlShape['formatMessage'],
) {
  const options: IEnumSelectOption<T>[] = values.map((value) => ({
    value,
    label: formatMessage({ id: `sorting.${value}` }),
  }));

  return {
    isSearchable: false,
    options,
    value: options.find((option) => option.value === activeValue) ?? null,
    onChange: (option: IEnumSelectOption<T>) => {
      if (option.value !== activeValue) onChange(option.value);
    },
  };
}
