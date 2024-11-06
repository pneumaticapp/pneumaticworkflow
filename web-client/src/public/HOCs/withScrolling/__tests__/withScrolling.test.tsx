import * as React from 'react';
import { shallow } from 'enzyme';
import { withScrolling } from '../withScrolling';

class MockComponent extends React.Component {
  public redner() {
    return <div />;
  }
}

describe('withScrolling', () => {
  it('upon initial rendering, nothing is scrolled to the top', () => {
    const WrapperComponent = withScrolling(MockComponent);
    const wrapper = shallow(<WrapperComponent />) as any;

    expect(wrapper.state().isOnTop).toBe(true);
  });

  it('subscribes to the scroll event', () => {
    const addEventListener = jest.spyOn(window, 'addEventListener');

    const WrapperComponent = withScrolling(MockComponent);
    const wrapper = shallow<any>(<WrapperComponent />);
    const instance = wrapper.instance() as any;

    expect(addEventListener).toHaveBeenCalledWith(
      'scroll',
      instance.throttledScrollingHandler,
    );
  });

  it('unsubscribes from the scroll event', () => {
    const removeEventListener = jest.spyOn(window, 'removeEventListener');

    const WrapperComponent = withScrolling(MockComponent);
    const wrapper = shallow<any>(<WrapperComponent />);
    const instance = wrapper.instance() as any;
    wrapper.unmount();

    expect(removeEventListener).toHaveBeenCalledWith(
      'scroll',
      instance.throttledScrollingHandler,
    );
  });

  describe('handleChangeScrolling', () => {
    it('updates the scroll flag if scrolled from the initial position', () => {
      const WrapperComponent = withScrolling(MockComponent);
      const wrapper = shallow<any>(<WrapperComponent />);

      const instance = wrapper.instance();
      const setState = jest.spyOn(instance, 'setState');

      setState.mockClear();

      wrapper.setState({ isOnTop: true });
      Object.defineProperty(window, 'pageYOffset', {
        get: () => 10,
      });
      instance.handleChangeScrolling();

      expect(setState).toHaveBeenCalledWith({ isOnTop: false });
    });

    it('updates the scroll flag if scrolled to the initial position', () => {
      const WrapperComponent = withScrolling(MockComponent);
      const wrapper = shallow<any>(<WrapperComponent />);

      const instance = wrapper.instance();
      const setState = jest.spyOn(instance, 'setState');

      setState.mockClear();

      wrapper.setState({ isOnTop: false });
      Object.defineProperty(window, 'pageYOffset', {
        get: () => 0,
      });
      instance.handleChangeScrolling();

      expect(setState).toHaveBeenCalledWith({ isOnTop: true });
    });
  });
});
