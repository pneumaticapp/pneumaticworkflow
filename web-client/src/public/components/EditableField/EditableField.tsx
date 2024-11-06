/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import * as classnames from 'classnames';
import styles from './EditableField.css';
import { onEnterPressed } from '../../utils/handlers';
import { Tooltip } from 'reactstrap';
import { IntlMessages } from '../IntlMessages';
import { sanitizeText } from '../../utils/strings';

export interface IEditableFieldProps {
  value: string;
  id: string;
  hiddenIcon?: boolean;
  changeValue(value: string): void;
  fieldClassName?: string;
  validate?(value: string): string;
}

export interface IEditableFieldState {
  isEditable: boolean;
  touched: boolean;
}

export class EditableField extends React.Component<IEditableFieldProps, IEditableFieldState> {
  public state = {
    isEditable: false,
    touched: false,
  };

  public shouldComponentUpdate(nextProps: IEditableFieldProps, nextState: IEditableFieldState): boolean {
    return !this.isTextEqual(nextProps.value, this.textContent) ||
      nextState.isEditable !== this.state.isEditable;
  }

  public fieldRef = React.createRef<HTMLSpanElement>();
  public render() {
    const {
      id,
      hiddenIcon,
      fieldClassName,
      value,
    } = this.props;
    const { isEditable } = this.state;
    const error = this.getError();

    return (
      <span
        id={id}
        className={classnames(
          styles['edit'],
          {[styles['edit--editable']]: isEditable, [styles['edit--hidden-icon']]: hiddenIcon},
        )}
      >
        <span
          className={classnames(styles['edit-field'], fieldClassName)}
          ref={this.fieldRef}
          contentEditable={isEditable}
          onBlur={this.blockEditable}
          onInput={this.handleChange}
          onKeyDown={onEnterPressed(this.blockEditable)}
          onClick={hiddenIcon ? this.onEditClick : undefined}
          suppressContentEditableWarning
        >
          {sanitizeText(value)}
        </span>
        {!hiddenIcon &&
          <i
            className={classnames('simple-icon-pencil', styles['edit-icon'])}
            onClick={this.onEditClick}
          />
        }
        {error &&
          <Tooltip
            placement="left"
            isOpen
            target={id}
          >
            <IntlMessages id={error}/>
          </Tooltip>
        }
      </span>
    );
  }

  private handleChange = (e: React.FormEvent) => {
    this.props.changeValue(sanitizeText(e.currentTarget.textContent));
  };

  private isTextEqual = (text1: string | null, text2: string | null) => {
    return sanitizeText(text1) === sanitizeText(text2);
  };

  private get textContent() {
    return this.fieldRef.current && this.fieldRef.current.textContent || '';
  }

  private getError = () => {
    const { validate } = this.props;
    const { touched } = this.state;
    const value = this.textContent;
    if (!validate || !touched) {
      return '';
    }

    return validate(value) || '';
  };

  private onEditClick = () => {
    if (!this.state.isEditable) {
      this.setState({isEditable: true}, this.handleCaret);
    }
  };

  private blockEditable = () => this.setState({isEditable: false, touched: true});

  private handleCaret = () => {
    const {current: element} = this.fieldRef;
    if (!element) {
      return;
    }
    element.focus();
    if (window.getSelection && document.createRange) {
      let range = document.createRange();
      range.selectNodeContents(element);
      range.collapse(false);
      let sel = window.getSelection();
      if (sel) {
        sel.removeAllRanges();
        sel.addRange(range);
      }
    }
  };
}
