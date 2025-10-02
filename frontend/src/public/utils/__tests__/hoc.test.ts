/* eslint-disable */
/* prettier-ignore */
/* tslint:disable:no-any */
import { getDisplayName } from '../hoc';

describe('hoc', () => {
  describe('getDisplayName', () => {
    it('accepts a component and returns its displayName', () => {
      const displayName = 'MyComponent';
      const MyComponet: any = {displayName};

      const result = getDisplayName(MyComponet);

      expect(result).toEqual(displayName);
    });
    it('accepts a component and returns its name property if displayName is not present', () => {
      const name = 'MyComponentName';
      const MyComponet: any = {name};

      const result = getDisplayName(MyComponet);

      expect(result).toEqual(name);
    });
    it('accepts a component and returns “Default” if there is no name property on the component', () => {
      const MyComponet: any = {};

      const result = getDisplayName(MyComponet);

      expect(result).toEqual('Component');
    });
  });
});
