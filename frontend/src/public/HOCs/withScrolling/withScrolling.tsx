/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { throttle } from 'throttle-debounce';
import { getWrappedDisplayName } from '../../utils/hoc';

export interface IWithScrollingProps {
  isOnTop: boolean;
}

export interface IWithScrollingState {
  isOnTop: boolean;
}

export function withScrolling<T>(Child: React.ComponentType<T>) {
  return class extends React.Component<T, IWithScrollingState> {
    public static displayName = getWrappedDisplayName(Child as React.ComponentType<{}>, 'withScrolling');

    public state = {
      isOnTop: false,
    };

    private handleChangeScrolling = () => {
      const { isOnTop: currentIsOnTop } = this.state;
      const newIsOnTop = window.pageYOffset === 0;

      if (currentIsOnTop !== newIsOnTop) {
        this.setState({ isOnTop: newIsOnTop });
      }
    };

    private throttledScrollingHandler = throttle(200, this.handleChangeScrolling);

    public componentDidMount() {
      window.addEventListener('scroll', this.throttledScrollingHandler);
      this.throttledScrollingHandler();
    }

    public componentWillUnmount() {
      window.removeEventListener('scroll', this.throttledScrollingHandler);
    }

    public render() {
      const { isOnTop } = this.state;

      return <Child {...this.props} isOnTop={isOnTop} />;
    }
  };
}
