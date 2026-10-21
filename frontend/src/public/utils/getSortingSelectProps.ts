import type { IntlShape } from 'react-intl';

interface ISortingOption<T extends string> {
  value: T;
  label: string;
}

export function getSortingSelectProps<T extends string>(
  values: T[],
  activeValue: T,
  onChange: (value: T) => void,
  formatMessage: IntlShape['formatMessage'],
) {
  const options: ISortingOption<T>[] = values.map((value) => ({
    value,
    label: formatMessage({ id: `sorting.${value}` }),
  }));

  return {
    isSearchable: false,
    options,
    value: options.find((option) => option.value === activeValue) ?? null,
    onChange: (option: ISortingOption<T>) => {
      if (option.value !== activeValue) onChange(option.value);
    },
  };
}
