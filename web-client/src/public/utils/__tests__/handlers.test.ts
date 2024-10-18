/* eslint-disable */
/* prettier-ignore */
/* tslint:disable:no-any */
import { EKeycodes, onKeyPressedCreator } from '../handlers';

describe('handlers', () => {
  describe('onKeyPressedCreator', () => {
    it('возвращает функцию, которая вызывает переданный в него колбек, если было событие о нажатии клавиши', () => {
      const callback = jest.fn();
      const event: any = {keyCode: EKeycodes.Escape};
      const onEscPressed = onKeyPressedCreator(EKeycodes.Escape);

      onEscPressed(callback)(event);

      expect(callback).toBeCalled();
    });
    it('не вызывает переданный в него колбек, если было событие о нажатии другой клавиши', () => {
      const callback = jest.fn();
      const event: any = {keyCode: 28};
      const onEscPressed = onKeyPressedCreator(EKeycodes.Escape);

      onEscPressed(callback)(event);

      expect(callback).not.toBeCalled();
    });
  });
});
