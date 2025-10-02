import React, { useState, useEffect, useRef, ReactNode, useCallback } from 'react';
import ReactDOM from 'react-dom';
import classnames from 'classnames';

import styles from './BaseModal.css';
import { ClearIcon } from '../../icons';

interface IBaseModalProps {
  isOpen: boolean;
  toggle?: () => void;
  backdropClassName?: string;
  wrapClassName?: string;
  className?: string;
  contentClassName?: string;
  centered?: boolean;
  backdrop?: boolean | 'static';
  zIndex?: number;
  children: ReactNode;
}

export function BaseModal({
  isOpen,
  toggle,
  className,
  backdropClassName,
  contentClassName,
  wrapClassName,
  centered = true,
  backdrop = true,
  zIndex = 1050,
  children,
}: IBaseModalProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [showClass, setShowClass] = useState(false);
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      setIsVisible(true);
      document.body.style.overflow = 'hidden';
      const timer = setTimeout(() => {
        setShowClass(true);
      }, 10);
      return () => clearTimeout(timer);
    }

    setShowClass(false);
    const timer = setTimeout(() => {
      setIsVisible(false);
      document.body.style.overflow = '';
    }, 150);
    return () => clearTimeout(timer);
  }, [isOpen]);

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen && backdrop !== 'static' && toggle) {
        toggle();
      }
    },
    [isOpen, backdrop, toggle],
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (backdrop !== 'static' && toggle && e.target === e.currentTarget) {
      toggle();
    }
  };

  if (!isVisible) {
    return null;
  }

  return ReactDOM.createPortal(
    <div className={wrapClassName}>
      <div
        className={classnames(styles['modal-backdrop'], styles['fade'], showClass && styles['show'], backdropClassName)}
        style={{ zIndex }}
        onClick={handleBackdropClick}
        role="button"
        tabIndex={0}
        onKeyDown={() => {}}
        aria-label="Close modal"
      />
      <div
        className={classnames(styles['modal'], styles['fade'], showClass && styles['show'])}
        style={{ zIndex: zIndex + 1 }}
      >
        <div
          className={classnames(styles['modal-dialog'], centered && styles['modal-dialog-centered'], className)}
          ref={modalRef}
        >
          <div className={classnames(styles['modal-content'], contentClassName)}>{children}</div>
        </div>
      </div>
    </div>,
    document.body,
  );
}

interface IModalPartProps {
  children?: ReactNode;
  className?: string;
  toggle?(): void;
  tag?: keyof JSX.IntrinsicElements;
}

export function ModalHeader({ children, className = '', toggle, tag: Tag = 'div' }: IModalPartProps) {
  return (
    <Tag className={classnames(styles['modal-header'], className)}>
      <p className={styles['title']}>{children}</p>
      {toggle && (
        <button type="button" onClick={toggle} className={styles['close-button']} aria-label="Close modal">
          <ClearIcon />
        </button>
      )}
    </Tag>
  );
}

export function ModalBody({ children, className = '', tag: Tag = 'div' }: IModalPartProps) {
  return <Tag className={classnames(styles['modal-body'], className)}>{children}</Tag>;
}

export function ModalFooter({ children, className = '', tag: Tag = 'div' }: IModalPartProps) {
  return <Tag className={classnames(styles['modal-footer'], className)}>{children}</Tag>;
}
