import * as React from 'react';

export const DropdownListMock = (props: {
  options?: Array<{ apiName?: string; value?: string; label?: React.ReactNode }>;
  value?: { apiName?: string; value?: string; label?: React.ReactNode } | null;
  onChange?: (option: { apiName?: string; value?: string; label?: React.ReactNode } | null) => void;
  isDisabled?: boolean;
  'aria-label'?: string;
  placeholder?: string;
}) => (
  <select
    aria-label={props['aria-label'] || 'operator'}
    disabled={props.isDisabled}
    value={props.value?.apiName ?? props.value?.value ?? ''}
    onChange={(event) => {
      const targetValue = event.target.value;
      const selectedOption = props.options?.find(
        (optionItem) => (optionItem.apiName ?? optionItem.value) === targetValue,
      );
      props.onChange?.(selectedOption || null);
    }}
  >
    {(props.placeholder || !props.value) && (
      <option value="">{props.placeholder || ''}</option>
    )}
    {props.options?.map((optionItem) => {
      const optionValue = optionItem.apiName ?? optionItem.value ?? '';
      return (
        <option key={optionValue} value={optionValue}>
          {typeof optionItem.label === 'string' ? optionItem.label : optionValue}
        </option>
      );
    })}
  </select>
);
