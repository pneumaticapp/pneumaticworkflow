/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
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
}

export interface ISideModalPartProps {
  children?: React.ReactNode;
  className?: string;
}

const Header = (props: ISideModalPartProps) => (
  <div className={classnames(styles['side-modal-parts_header'], props.className)}>
    {props.children}
  </div>
);

const Body = (props: ISideModalPartProps) => (
  <div className={classnames(styles['side-modal-parts_body'], props.className)}>
    {props.children}
  </div>
);

const Footer = (props: ISideModalPartProps) => (
  <div className={classnames(styles['side-modal-parts_footer'], props.className)}>
    {props.children}
  </div>
);

export class SideModal extends React.Component<ISideModalProps> {
  public static Header = Header;
  public static Body = Body;
  public static Footer = Footer;

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

  private renderModal() {
    const {
      className,
      isClosing,
      onClose,
    } = this.props;

    return (
      <OutsideClickHandler onOutsideClick={this.hanldeClickOutside}>
        <div className={classnames(
          styles['side-modal'],
          !isClosing ? styles['side-modal_opened'] : styles['side-modal_closed'],
        )}>
          <button
            onClick={onClose}
            type="button"
            className={styles['side-modal_close']}
            aria-label="Close modal"
            data-test-id="close"
          >
            <ClearIcon />
          </button>

          <div className={classnames(styles['side-modal-parts'], className)}>
            {this.props.children}
          </div>
        </div>
      </OutsideClickHandler>
    );
  }

  public render() {
    return ReactDOM.createPortal(this.renderModal(), document.body);
  }
}
