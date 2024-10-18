/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { useIntl } from 'react-intl';
import { useDispatch } from 'react-redux';

import { validateInviteEmail } from '../../../utils/validators';
import { Button, InputField } from '../../UI';
import { DropdownArea } from '../../UI/DropdownArea';
import { addTaskGuest } from '../../../redux/actions';
import { autoFocusFirstField } from '../../../utils/autoFocusFirstField';

import styles from './GuestsController.css';

interface IGuestControllerProps {
  taskId: number;
  className?: string;
}

export type IGuestControllerHandle = {
  updateDropdownPosition(): void;
};

export const GuestController = React.forwardRef<
IGuestControllerHandle,
IGuestControllerProps
>(({ taskId, className }, ref) => {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const containerRef = React.useRef(null);
  const [inputValue, setInputValue] = React.useState('');
  const [error, setError] = React.useState('');
  const [isLoading, setIsLoading] = React.useState(false);
  const dropdownRef = React.useRef<React.ElementRef<typeof DropdownArea> | null>(null);
  const handleChange = (e: React.FormEvent<HTMLInputElement>) => {
    setError('');
    setInputValue(e.currentTarget.value);
  };

  React.useImperativeHandle(ref, () => ({
    updateDropdownPosition: dropdownRef.current?.updateDropdownPosition || (() => {}),
  }));
  const addGuest = React.useCallback<React.FormEventHandler<HTMLFormElement>>(event => {
    event.preventDefault();

    if (isLoading) {
      return;
    }

    const error = validateInviteEmail(inputValue);
    if (error) {
      setError(error);

      return;
    }

    dispatch(addTaskGuest({
      taskId,
      guestEmail: inputValue,
      onStartUploading: () => setIsLoading(true),
      onEndUploading: () => setIsLoading(false),
      onError: () => setIsLoading(false),
    }));

    setInputValue('');
  }, [inputValue, setError]);

  return (
    <DropdownArea
      ref={dropdownRef}
      title={formatMessage({id: 'task.add-guest'})}
      containerClassName={className}
      onOpen={() => autoFocusFirstField(containerRef.current)}
    >
      <div className={styles['container']} ref={containerRef}>
        <div className={styles['help']}>
          {formatMessage({id: 'task.add-guest-help-text'})}{' '}
          <a
            href="https://support.pneumatic.app/en/articles/6145048-free-external-users"
            target="_blank"
            className={styles['link']}
          >
            {formatMessage({id: 'general.learn-more'})}
          </a>
        </div>
        <form onSubmit={addGuest} className={styles['form']} data-autofocus-first-field={true}>
          <InputField
            value={inputValue}
            onChange={handleChange}
            errorMessage={error}
            placeholder={formatMessage({id: 'task.add-guest-field-placeholder'})}
            fieldSize="md"
          />
          <Button
            type="submit"
            label={formatMessage({id: 'task.add-guest-add-button'})}
            buttonStyle="yellow"
            size="md"
            className={styles['add-btn']}
            isLoading={isLoading}
          />
        </form>
      </div>
    </DropdownArea>
  );
});
