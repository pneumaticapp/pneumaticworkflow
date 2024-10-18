/* eslint-disable jsx-a11y/no-static-element-interactions */
/* eslint-disable jsx-a11y/click-events-have-key-events */
/* eslint-disable react/no-unused-class-component-methods */
/* eslint-disable react/default-props-match-prop-types */
import * as React from 'react';
import * as classNames from 'classnames';
import { IntlShape } from 'react-intl';

import { ETimeouts } from '../../../constants/defaultValues';
import { noop } from '../../../utils/noop';
import { TNotificationType } from '../../../types';
import { ClearIcon } from '../../icons';

import styles from './Notifications.css';

interface INotificationProps {
  type: TNotificationType;
  title: React.ReactNode | string | null;
  message: React.ReactNode | string | null;
  timeOut: number;
  onClick: Function;
  onCancelClick?: Function;
  onRequestHide: Function;
  onSubmitClick?: Function;
  customClassName: string;
  intl: IntlShape;
}

export class Notification extends React.Component<INotificationProps> {
  private timer: number | undefined;

  public static defaultProps = {
    type: 'info',
    title: null,
    message: null,
    timeOut: ETimeouts.Short,
    onClick: noop,
    onRequestHide: noop,
    customClassName: '',
  };

  public componentDidMount() {
    const { timeOut } = this.props;
    if (timeOut !== 0) {
      this.timer = window.setTimeout(this.requestHide, timeOut);
    }
  }

  public componentWillUnmount() {
    if (this.timer) {
      clearTimeout(this.timer);
    }
  }

  public handleClick = () => {
    const { onClick } = this.props;
    if (onClick) {
      onClick();
    }
    this.requestHide();
  };

  public handleCancelClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    const { onCancelClick } = this.props;
    if (onCancelClick) {
      onCancelClick();
    }
    this.requestHide();
  };

  public handleSubmitClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    const { onSubmitClick } = this.props;
    if (onSubmitClick) {
      onSubmitClick();
    }
    this.requestHide();
  };

  public handleClose = (e: React.MouseEvent) => {
    e.stopPropagation();
    this.requestHide();
  };

  public requestHide = () => {
    const { onRequestHide } = this.props;
    if (onRequestHide) {
      onRequestHide();
    }
  };

  public render() {
    const {
      customClassName,
      type,
      intl: { messages, formatMessage },
    } = this.props;
    let { title, message } = this.props;

    if (typeof title === 'string') {
      title = messages[title] || title;
    }
    if (typeof message === 'string') {
      message = messages[message] || message;
    }
    const className = classNames(['notification', `notification-${type}`, customClassName]);
    title = title ? <h4 className="title">{title}</h4> : null;

    return (
      <div className={className} onClick={this.handleClick}>
        <div className="notification-message" role="alert">
          {title}
          <div className="message">{message}</div>

          <button
            onClick={this.handleClose}
            type="button"
            className={styles['close-button']}
            aria-label={formatMessage({ id: 'notifications.hide' })}
          >
            <ClearIcon />
          </button>
          <div className="close-notification" onClick={this.handleClose} />
        </div>
      </div>
    );
  }
}
