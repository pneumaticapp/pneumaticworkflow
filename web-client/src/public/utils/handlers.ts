/* eslint-disable indent */
import { KeyboardEvent } from 'react';

export const enum EKeycodes {
  Enter = 13,
  ArrowDown = 40,
  ArrowUp = 38,
  Escape = 27,
}

export const onKeyPressedCreator =
  (keyCode: EKeycodes) =>
  (fn?: Function) =>
  <T>(e: KeyboardEvent<T>) => {
    if (e.keyCode === keyCode && typeof fn === 'function' && !e.shiftKey) {
      fn();
    }
  };
export const onEscPressed = onKeyPressedCreator(EKeycodes.Escape);
export const onEnterPressed = onKeyPressedCreator(EKeycodes.Enter);

const isTrailingDotZeros = /[.,]0*$/;
export const removeTrailingDotZeros = (
  value: string,
  onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void,
): void => {
  if (isTrailingDotZeros.test(value)) {
    const cleanedValue = value.replace(isTrailingDotZeros, '');
    onChange({
      target: { value: cleanedValue },
    } as React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>);
  }
};
