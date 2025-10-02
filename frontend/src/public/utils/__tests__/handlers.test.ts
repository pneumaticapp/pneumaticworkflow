/* eslint-disable */
/* prettier-ignore */
/* tslint:disable:no-any */
import { EKeycodes, onKeyPressedCreator } from '../handlers';

describe('handlers', () => {
  describe('onKeyPressedCreator', () => {
    it('returns a function that calls the passed callback if a key press event occurs', () => {
      const callback = jest.fn();
      const event: any = {keyCode: EKeycodes.Escape};
      const onEscPressed = onKeyPressedCreator(EKeycodes.Escape);

      onEscPressed(callback)(event);

      expect(callback).toBeCalled();
    });
    it('does not call the passed callback if a different key press event occurs', () => {
      const callback = jest.fn();
      const event: any = {keyCode: 28};
      const onEscPressed = onKeyPressedCreator(EKeycodes.Escape);

      onEscPressed(callback)(event);

      expect(callback).not.toBeCalled();
    });
  });
});
