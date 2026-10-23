import * as React from 'react';
import { useEffect, useRef } from 'react';
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

export function TemplateValidationError({ apiNames, className }: ITemplateValidationErrorProps) {
  const dispatch = useDispatch();
  const validationErrors = useSelector(getTemplateValidationErrors);
  const batchId = useSelector(getTemplateValidationBatchId);
  const focusApiName = useSelector(getTemplateValidationFocusApiName);
  const errorRef = useRef<HTMLParagraphElement>(null);

  const validationError = validationErrors.find(({ target }) => apiNames.includes(target.elementApiName));
  const isFocused = validationError?.target.elementApiName === focusApiName;

  useEffect(() => {
    if (!isFocused) return;

    errorRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    dispatch(clearTemplateValidationFocus());
  }, [isFocused, batchId, dispatch]);

  if (!validationError) return null;

  return (
    <p ref={errorRef} role="alert" className={classnames(styles['error'], className)}>
      {validationError.message}
    </p>
  );
}
