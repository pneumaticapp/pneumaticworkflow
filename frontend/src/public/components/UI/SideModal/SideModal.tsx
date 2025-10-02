import * as React from 'react';
import { Component } from 'react';
import classnames from 'classnames';
import * as ReactDOM from 'react-dom';
import OutsideClickHandler from 'react-outside-click-handler';

import { ClearIcon } from '../../icons';
import { history } from '../../../utils/history';

import styles from './SideModal.css';

export interface ISideModalProps {
  isClosing?: boolean;
  className?: string;
  onOpen?(): void;
  onClose(): void;
  onAfterClose?(): void;
  nonePeddingRight?: boolean;
}

export interface ISideModalPartProps {
  children?: React.ReactNode;
  className?: string;
}

const Header = (props: ISideModalPartProps) => {
  const { children, className } = props;
  return <div className={classnames(styles['side-modal-parts_header'], className)}>{children}</div>;
};

const Body = (props: ISideModalPartProps) => {
  const { children, className } = props;
  return <div className={classnames(styles['side-modal-parts_body'], className)}>{children}</div>;
};

const Footer = (props: ISideModalPartProps) => {
  const { children, className } = props;
  return <div className={classnames(styles['side-modal-parts_footer'], className)}>{children}</div>;
};

export class SideModal extends Component<ISideModalProps> {
  public static Header = Header;

  public static Body = Body;

  public static Footer = Footer;

  public componentDidMount() {
    const { onOpen, onClose } = this.props;
    window.addEventListener('keydown', this.handleKeyDown);
    onOpen?.();

    history.listen(() => {
      onClose();
    });
  }

  public componentWillUnmount() {
    const { onAfterClose } = this.props;
    window.removeEventListener('keydown', this.handleKeyDown);
    onAfterClose?.();
  }

  private hanldeClickOutside = () => {
    const { onClose } = this.props;

    onClose();
  };

  private handleKeyDown = (event: KeyboardEvent) => {
    const ESC_CODE = 27;

    const { onClose } = this.props;

    if (event.keyCode === ESC_CODE) {
      onClose();
    }
  };

  private renderModal() {
    const { className, isClosing, onClose, nonePeddingRight, children } = this.props;

    return (
      <OutsideClickHandler onOutsideClick={this.hanldeClickOutside}>
        <div
          className={classnames(
            styles['side-modal'],
            !isClosing ? styles['side-modal_opened'] : styles['side-modal_closed'],
            nonePeddingRight && styles['side-modal_none-pedding-right'],
          )}
        >
          <button
            onClick={onClose}
            type="button"
            className={classnames(
              styles['side-modal_close'],
              nonePeddingRight && styles['side-modal_close-is-from-view-modal'],
            )}
            aria-label="Close modal"
            data-test-id="close"
          >
            <ClearIcon />
          </button>

          <div className={classnames(styles['side-modal-parts'], className)}>{children}</div>
        </div>
      </OutsideClickHandler>
    );
  }

  public render() {
    return ReactDOM.createPortal(this.renderModal(), document.body);
  }
}
