/* eslint-disable react/default-props-match-prop-types */
import * as React from 'react';
import { TransitionGroup, CSSTransition } from 'react-transition-group';
import { injectIntl, IntlShape } from 'react-intl';
import * as classNames from 'classnames';

import { Notification } from './Notification';
import { INotification } from '../../../types';
import { noop } from '../../../utils/noop';
import { isArrayWithItems } from '../../../utils/helpers';

export interface INotificationsProps {
  notifications: INotification[];
  onRequestHide: Function;
  enterTimeout: number;
  leaveTimeout: number;
  intl: IntlShape;
}

export class Notifications extends React.Component<INotificationsProps> {
  public static defaultProps = {
    notifications: [],
    onRequestHide: noop,
    enterTimeout: 400,
    leaveTimeout: 0,
  };

  public handleRequestHide = (notification: INotification) => () => {
    const { onRequestHide } = this.props;
    if (onRequestHide) {
      onRequestHide(notification);
    }
  };

  public renderNotifiactons = () => {
    const { notifications, enterTimeout, leaveTimeout, intl } = this.props;

    if (!isArrayWithItems(notifications)) {
      return null;
    }

    return notifications.map((notification) => {
      const key = notification.id || new Date().getTime();

      return (
        <CSSTransition classNames="notification" key={key} timeout={{ exit: leaveTimeout, enter: enterTimeout }}>
          <Notification
            key={key}
            intl={intl}
            type={notification.type}
            title={notification.title}
            message={notification.message}
            timeOut={notification.timeOut}
            onClick={notification.onClick}
            onCancelClick={notification.onCancelClick}
            onSubmitClick={notification.onSubmitClick}
            onRequestHide={this.handleRequestHide(notification)}
            customClassName={notification.customClassName}
          />
        </CSSTransition>
      );
    });
  };

  public render() {
    const className = classNames('notification-container');

    return (
      <div className={className}>
        <TransitionGroup id="notification-container">{this.renderNotifiactons()}</TransitionGroup>
      </div>
    );
  }
}

export const NotificationsIntl = injectIntl(Notifications);
