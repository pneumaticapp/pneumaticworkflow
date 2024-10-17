/* eslint-disable */
/* prettier-ignore */
/* tslint:disable:no-any */
import { getDisplayName } from '../hoc';

describe('hoc', () => {
  describe('getDisplayName', () => {
    it('принимает компонент и возвращает его displayName', () => {
      const displayName = 'MyComponent';
      const MyComponet: any = {displayName};

      const result = getDisplayName(MyComponet);

      expect(result).toEqual(displayName);
    });
    it('принимает компонент и возвращает свойство name, если нет displayName', () => {
      const name = 'MyComponentName';
      const MyComponet: any = {name};

      const result = getDisplayName(MyComponet);

      expect(result).toEqual(name);
    });
    it('принимает компонент и возвращает по умолчанию если нет названия Component', () => {
      const MyComponet: any = {};

      const result = getDisplayName(MyComponet);

      expect(result).toEqual('Component');
    });
  });
});
