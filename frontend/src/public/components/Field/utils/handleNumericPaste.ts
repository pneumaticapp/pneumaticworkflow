import type { ChangeEvent } from 'react';

/**
 * Handles paste in numeric field: replaces comma with dot.
 * May cause validation line flicker.
 */
export function handleNumericPaste(
  e: React.ClipboardEvent,
  input: HTMLInputElement,
  onChange: (event: ChangeEvent<HTMLInputElement>) => void,
  name: string,
): void {
  const text = e.clipboardData.getData('Text');
  if (!text.includes(',')) return;

  e.preventDefault();

  const currentValue = input.value;
  const selStart = input.selectionStart ?? 0;
  const selEnd = input.selectionEnd ?? 0;

  let firstSeparatorIndex = text.indexOf(',');
  const firstDotIndex = text.indexOf('.');
  if (firstDotIndex !== -1 && firstDotIndex < firstSeparatorIndex) {
    firstSeparatorIndex = firstDotIndex;
  }
  const processedText = `${text.substring(0, firstSeparatorIndex)}.${text
    .substring(firstSeparatorIndex + 1)
    .replace(/,/g, '')}`;

  const hasDecimalSeparator = currentValue.includes('.');
  const decimalPosition = currentValue.indexOf('.');
  let newValue: string;
  if (hasDecimalSeparator && selStart <= decimalPosition) {
    newValue =
      currentValue.substring(0, selStart) +
      processedText +
      currentValue.substring(selEnd).replace(/\./g, '');
  } else if (!hasDecimalSeparator) {
    newValue = currentValue.substring(0, selStart) + processedText + currentValue.substring(selEnd);
  } else {
    newValue = currentValue.substring(0, selStart) + text + currentValue.substring(selEnd);
  }

  onChange({
    target: {
      value: newValue,
      name,
      type: 'text',
    },
  } as ChangeEvent<HTMLInputElement>);
}
