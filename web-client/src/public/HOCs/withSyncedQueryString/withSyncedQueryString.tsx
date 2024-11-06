/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { AnyAction, Dispatch } from 'redux';
import { connect } from 'react-redux';
import { RouteComponentProps, withRouter } from 'react-router-dom';

import { getQueryStringByParams, getQueryStringParams, history } from '../../utils/history';
import { getWrappedDisplayName } from '../../utils/hoc';
import { isArrayWithItems } from '../../utils/helpers';

const HOC_WRAPPER_NAME = 'withSyncedQueryString';

export interface IQuerySyncItem<TProps> {
  /**
   * Name of prop that will be synced with query string parameter
   */
  propName: keyof TProps;

  /**
   * Name of query string parameter (could be any string)
   */
  queryParamName: string;

  /**
   * Creator of action that will be dispatched when query string parameter changes
   */
  createAction(queryParam: string): AnyAction;

  /**
   * Action that will be dispatched when query string parameter is empty
   */
  defaultAction: AnyAction;

  /**
   * Returns a new query string parameter by synced prop value
   */
  // tslint:disable-next-line: no-any
  getQueryParamByProp(propValue: any): string;
}

export interface ISyncedQueryStringState {
  isMounted: boolean;
}

export const withSyncedQueryString =
  <T extends {}>(settings: IQuerySyncItem<T>[], resetAction?: AnyAction) =>
  (Child: React.ComponentType<T>): React.ComponentType => {
    type TWrappedChildProps = T & RouteComponentProps & { dispatch: Dispatch };

    const wrpappedChild = class extends React.Component<TWrappedChildProps, ISyncedQueryStringState> {
      public static displayName = getWrappedDisplayName(Child, HOC_WRAPPER_NAME);

      public state: ISyncedQueryStringState = {
        isMounted: false,
      };

      public componentDidMount() {
        const currentSyncSettings = settings.filter(({ queryParamName }) => {
          return Boolean(this.currentSearchParams[queryParamName]);
        });

        // clear initial redux store
        if (isArrayWithItems(currentSyncSettings) && resetAction) {
          this.props.dispatch(resetAction);
        }

        this.updateStoreBySettings(currentSyncSettings);
        this.handleUpdateLocation();
        this.setState({ isMounted: true });
      }

      public componentDidUpdate(prevProps: TWrappedChildProps) {
        const watchPropsChanged = settings.some(({ propName }) => prevProps[propName] !== this.props[propName]);

        if (watchPropsChanged) {
          this.handleUpdateLocation();
        }
      }

      private get currentSearchParams() {
        return getQueryStringParams(this.props.location.search);
      }

      public handleUpdateState = (prevProps: TWrappedChildProps) => {
        const prevParams = getQueryStringParams(prevProps.location.search);

        const changedQueryParamSettings = settings.filter(({ queryParamName }) => {
          return this.currentSearchParams[queryParamName] !== prevParams[queryParamName];
        });

        this.updateStoreBySettings(changedQueryParamSettings);
      };

      public handleUpdateLocation = () => {
        const queryParams = settings.reduce((acc, setting) => {
          const { propName, queryParamName, getQueryParamByProp } = setting;

          const propValue = this.props[propName];
          const queryParamValue = getQueryParamByProp(propValue);

          return { ...acc, [queryParamName]: queryParamValue };
        }, {});

        const newQueryString = getQueryStringByParams(queryParams);

        history.push({ search: newQueryString });
      };

      private updateStoreBySettings = (settings: IQuerySyncItem<T>[]) => {
        const actions = this.getActionsToSyncState(settings);

        actions.forEach(this.props.dispatch);
      };

      public getActionsToSyncState = (settings: IQuerySyncItem<T>[]) => {
        const currentParams = getQueryStringParams(this.props.location.search);

        const actions = settings.map((syncSetting) => {
          const { queryParamName, defaultAction, createAction } = syncSetting;
          const newQueryParamValue = currentParams[queryParamName];

          return newQueryParamValue ? createAction(newQueryParamValue) : defaultAction;
        });

        return actions;
      };

      public render() {
        const { isMounted } = this.state;

        if (!isMounted) {
          return null;
        }

        return <Child {...this.props} />;
      }
    };

    const WrpappedChildWithRouter = withRouter(wrpappedChild) as React.ComponentType;

    return connect(null)(WrpappedChildWithRouter);
  };
