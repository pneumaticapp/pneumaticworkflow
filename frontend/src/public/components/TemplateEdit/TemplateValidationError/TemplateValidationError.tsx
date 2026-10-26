import * as React from 'react';
import { useEffect, useRef } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';
import classnames from 'classnames';

import {
  getTemplateValidationBatchId,
  getTemplateValidationErrors,
  getTemplateValidationFocusApiName,
} from '../../../redux/selectors/templateValidation';
import { clearTemplateValidationFocus } from '../../../redux/templateValidation/slice';
import type { ITemplateValidationErrorProps } from './types';

import styles from './TemplateValidationError.css';

export function TemplateValidationError({ apiNames, section, className }: ITemplateValidationErrorProps) {
  const { messages, formatMessage } = useIntl();
  const dispatch = useDispatch();
  const validationErrors = useSelector(getTemplateValidationErrors);
  const batchId = useSelector(getTemplateValidationBatchId);
  const focusApiName = useSelector(getTemplateValidationFocusApiName);
  const errorRef = useRef<HTMLParagraphElement>(null);

  const validationError = validationErrors.find(
    ({ target }) => apiNames.includes(target.elementApiName) && (section === undefined || target.section === section),
  );
  const isFocused = validationError?.target.elementApiName === focusApiName;

  useEffect(() => {
    if (!isFocused) return;

    errorRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    dispatch(clearTemplateValidationFocus());
  }, [isFocused, batchId, dispatch]);

  if (!validationError) return null;

  return (
    <p ref={errorRef} role="alert" className={classnames(styles['error'], className)}>
      {messages[validationError.message] ? formatMessage({ id: validationError.message }) : validationError.message}
    </p>
  );
}
