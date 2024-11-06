/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import * as classnames from 'classnames';
import { Link } from 'react-router-dom';

import styles from './SideModalCard.css';

export interface ISideModalCardProps {
  className?: string;
  onClick?(): void;
  route?: string;
}

export interface ISideModalCardPartProps {
  children: React.ReactNode;
  className?: string;
}

const Title = (props: ISideModalCardPartProps) => (
  <div className={classnames(styles['card__title'], props.className)}>{props.children}</div>
);

const Body = (props: ISideModalCardPartProps) => <div className={props.className}>{props.children}</div>;

const Footer = (props: ISideModalCardPartProps) => (
  <div className={classnames(styles['card__footer'], props.className)}>{props.children}</div>
);

export class SideModalCard extends React.Component<ISideModalCardProps> {
  public static Title = Title;
  public static Body = Body;
  public static Footer = Footer;

  private renderCard() {
    const { children, className, route, onClick } = this.props;

    if (route) {
      return (
        <Link className={classnames(className, styles['card-container'])} to={route} onClick={onClick}>
          {children}
        </Link>
      );
    }

    return (
      <div role="button" className={classnames(className, styles['card-container'])} onClick={onClick}>
        {children}
      </div>
    );
  }

  public render() {
    return this.renderCard();
  }
}
