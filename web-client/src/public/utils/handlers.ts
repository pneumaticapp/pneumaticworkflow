import * as React from 'react';

export const enum EKeycodes {
  Enter = 13,
  ArrowDown = 40,
  ArrowUp = 38,
  Escape = 27,
}

export const onKeyPressedCreator = (keyCode: EKeycodes) => (fn?: Function) => <T>(e: React.KeyboardEvent<T>) => {
  if (e.keyCode === keyCode && typeof fn === 'function' && !e.shiftKey) {
    fn();
  }
};
export const onEscPressed = onKeyPressedCreator(EKeycodes.Escape);
export const onEnterPressed = onKeyPressedCreator(EKeycodes.Enter);
