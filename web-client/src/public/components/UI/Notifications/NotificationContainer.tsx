/* eslint-disable class-methods-use-this */
/* eslint-disable react/default-props-match-prop-types */
/* eslint-disable react/sort-comp */
import * as React from 'react';
import { NotificationManager } from './NotificationManager';
import { NotificationsIntl } from './Notifications';
import { INotification } from '../../../types';

export interface INotificationContainerProps {
  enterTimeout: number;
  leaveTimeout: number;
}

export interface INotificationContainerState {
  notifications: INotification[];
}

export class NotificationContainer extends React.Component<INotificationContainerProps> {
  public constructor(props: INotificationContainerProps) {
    super(props);
    NotificationManager.addChangeListener(this.handleStoreChange);
  }

  public static defaultProps = {
    enterTimeout: 400,
    leaveTimeout: 0,
  };

  public state = {
    notifications: [],
  };

  public componentWillUnmount() {
    NotificationManager.removeChangeListener(this.handleStoreChange);
  }

  public handleStoreChange = (notifications: INotification[]) => {
    this.setState({
      notifications,
    });
  };

  public handleRequestHide = (notification: INotification) => {
    NotificationManager.remove(notification);
  };

  public render() {
    const { notifications } = this.state;
    const { enterTimeout, leaveTimeout } = this.props;

    return (
      <NotificationsIntl
        enterTimeout={enterTimeout}
        leaveTimeout={leaveTimeout}
        notifications={notifications}
        onRequestHide={this.handleRequestHide}
      />
    );
  }
}
