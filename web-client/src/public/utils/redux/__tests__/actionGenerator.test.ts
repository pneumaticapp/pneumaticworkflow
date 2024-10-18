/* eslint-disable */
/* prettier-ignore */
import { actionGenerator } from '../actionGenerator';

describe('utils', () => {
  describe('redux', () => {
    describe('actionGenerator', () => {
      it('Создает redux action', () => {
        const type = 'FOO';
        const payload = 'BAR';
        const actionCreator = actionGenerator<'FOO', string>(type);

        const action = actionCreator(payload);

        expect(action).toEqual({
          type: 'FOO',
          payload: 'BAR',
        });
      });

      it('Создает простой action, без данных', () => {
        const type = 'FOO';
        const actionCreator = actionGenerator<'FOO'>(type);

        expect(actionCreator()).toEqual({ type: 'FOO' });
      });
    });
  });
});
