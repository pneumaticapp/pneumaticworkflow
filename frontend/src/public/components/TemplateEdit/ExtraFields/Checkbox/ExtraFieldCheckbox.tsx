/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import classnames from 'classnames';
import AutosizeInput from 'react-input-autosize';

import { getEmptySelection } from '../../KickoffRedux/utils/getEmptySelection';
import { validateCheckboxAndRadioField, validateKickoffFieldName } from '../../../../utils/validators';
import { IntlMessages } from '../../../IntlMessages';
import { EExtraFieldMode, IExtraFieldSelection, TExtraFieldMultipleValue } from '../../../../types/template';
import { fitInputWidth } from '../utils/fitInputWidth';
import { PencilSmallIcon, RemoveIcon } from '../../../icons';
import { Checkbox } from '../../../UI/Fields/Checkbox';
import { isArrayWithItems } from '../../../../utils/helpers';

import { IWorkflowExtraFieldProps } from '..';

import styles from '../../KickoffRedux/KickoffRedux.css';
import fieldStyles from './ExtraFieldCheckbox.css';

const DEFAULT_OPTION_INPUT_WIDTH = 120;
const DEFAULT_FIELD_INPUT_WIDTH = 120;

export function ExtraFieldCheckbox({
  field: { selections, isRequired = false, name, value },
  intl,
  namePlaceholder = intl.formatMessage({ id: 'template.kick-off-form-field-name-placeholder' }),
  mode = EExtraFieldMode.Kickoff,
  deleteField,
  editField,
  isDisabled = false,
}: IWorkflowExtraFieldProps) {
  const selectedOptions = value as TExtraFieldMultipleValue;

  const fieldNameInputRef = React.useRef<HTMLInputElement | null>(null);
  const optionInputsRefs = React.useRef<HTMLInputElement[]>([]);
  const [isFocused, setIsFocused] = React.useState(false);

  React.useEffect(() => {
    optionInputsRefs.current.forEach((input) => fitInputWidth(input, DEFAULT_OPTION_INPUT_WIDTH));
  }, [selections]);

  React.useEffect(() => {
    fitInputWidth(fieldNameInputRef.current, DEFAULT_FIELD_INPUT_WIDTH);
  }, []);

  const [activeOptionIndex, setActiveOptionIndex] = React.useState<number | null>(null);

  const fieldNameErrorMessage = validateKickoffFieldName(name) || '';
  const isKickoffFieldNameValid = !Boolean(fieldNameErrorMessage);

  const renderKickoffField = () => {
    const fieldNameClassName = classnames(fieldStyles['kickoff-create-field-name']);

    return (
      <div className={fieldStyles['kickoff-create-field-container']}>
        <div className={fieldNameClassName}>
          <AutosizeInput
            inputRef={(ref) => (fieldNameInputRef.current = ref)}
            inputClassName={classnames(
              fieldStyles['kickoff-create-field-name-input'],
              !isKickoffFieldNameValid && fieldStyles['kickoff-create-field-name-input_error'],
            )}
            onChange={handleChangeName}
            placeholder={namePlaceholder}
            type="text"
            value={name}
            disabled={isDisabled}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                setIsFocused(false);
                event.currentTarget.blur();
              }
            }}
          />
          {isRequired && <span className={styles['kick-off-required-sign']} />}
          {!isFocused && mode === EExtraFieldMode.Kickoff && (
            <button
              onClick={() => fieldNameInputRef.current?.focus()}
              className={classnames(styles['kick-off-edit-name'], fieldStyles['edit-name-button'])}
            >
              <PencilSmallIcon />
            </button>
          )}
        </div>

        {!isKickoffFieldNameValid && (
          <p className={fieldStyles['kickoff-create-field-container__error-message']}>
            <IntlMessages id={fieldNameErrorMessage} />
          </p>
        )}

        {selections && (
          <ul className={fieldStyles['kickoff-create-field-options']}>{selections?.map(renderKickoffOption)}</ul>
        )}

        {!isDisabled && (
          <button type="button" className={fieldStyles['kickoff-create-field-add-option']} onClick={handleAddOption}>
            <IntlMessages id="template.kick-off-add-options" />
          </button>
        )}
      </div>
    );
  };

  const renderKickoffOption = (field: IExtraFieldSelection, optionIndex: number) => {
    const { value } = field;

    const isActive = optionIndex === activeOptionIndex;
    const errorMessageIntl = validateCheckboxAndRadioField(value);
    const shouldShowError = Boolean(errorMessageIntl);

    return (
      <li
        key={optionIndex}
        className={fieldStyles['kickoff-create-field-option']}
        onMouseOver={() => setActiveOptionIndex(optionIndex)}
        onMouseLeave={() => setActiveOptionIndex(null)}
      >
        <div className={fieldStyles['kickoff-create-field-option__labeled-checkbox']}>
          <Checkbox
            title=""
            checked={false}
            disabled
            id={`extra-field-checkbox-${optionIndex}`}
            containerClassName={fieldStyles['labeled-checkbox__checkbox']}
          />
          <input
            ref={(el) => (optionInputsRefs.current[optionIndex] = el as HTMLInputElement)}
            className={fieldStyles['labeled-checkbox__input']}
            onChange={handleChangeOption(optionIndex)}
            placeholder={namePlaceholder}
            type="text"
            value={value}
            disabled={isDisabled}
          />
          <span className={fieldStyles['measure']} />
          {isActive && !isDisabled && (
            <div
              role="button"
              className={fieldStyles['labeled-checkbox__remove']}
              onClick={handleRemoveOption(optionIndex)}
            >
              <RemoveIcon />
            </div>
          )}
        </div>
        {shouldShowError && (
          <p className={fieldStyles['kickoff-set-field-option__error-text']}>
            <IntlMessages id={errorMessageIntl} />
          </p>
        )}
      </li>
    );
  };

  const handleChangeName = React.useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      fitInputWidth(e.target, DEFAULT_FIELD_INPUT_WIDTH);
      editField({ name: e.target.value });
    },
    [editField],
  );

  const handleDeleteField = React.useCallback(() => {
    if (!deleteField) {
      return;
    }

    deleteField();
  }, [deleteField]);

  const handleAddOption = () => {
    const newOptions = [...(selections as IExtraFieldSelection[]), getEmptySelection()];
    editField({ selections: newOptions });
  };

  const handleRemoveOption = (optionIndex: number) => () => {
    const newOptions = selections?.filter((_, index) => index !== optionIndex);

    const isNoOptions = !isArrayWithItems(newOptions);

    isNoOptions ? handleDeleteField() : editField({ selections: newOptions });
  };

  const handleChangeOption = (optionIndex: number) => (event: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = event.target.value;

    const newOptions = selections?.map((option, index) => {
      if (index === optionIndex) {
        return { ...option, value: newValue };
      }

      return option;
    });

    editField({ selections: newOptions });
  };

  const renderProcessRunOption = ({ id: optionId, value, apiName }: IExtraFieldSelection) => {
    const isChecked = selectedOptions && selectedOptions.includes(apiName);

    return (
      <li key={optionId} className={fieldStyles['kickoff-set-field-option']}>
        <Checkbox id={String(apiName)} title={value} onChange={handleToggleOption(apiName)} checked={isChecked} />
      </li>
    );
  };

  const renderProcessRunField = () => {
    if (!selections) {
      return null;
    }

    const fieldNameClassName = classnames(fieldStyles['kickoff-set-field-name']);

    return (
      <div className={fieldStyles['kickoff-set-field-container']} data-autofocus-first-field={true}>
        <div>
          <div className={fieldNameClassName}>{name}</div>
          {isRequired && <span className={styles['kick-off-required-sign']} />}
        </div>

        <ul className={fieldStyles['kickoff-set-field-options']}>{selections.map(renderProcessRunOption)}</ul>
      </div>
    );
  };

  const handleToggleOption = (apiName: string) => () => {
    const isChecked = selectedOptions && !selectedOptions.includes(apiName);

    const newOptions = isChecked
      ? [...selectedOptions, apiName]
      : selectedOptions.filter((itemApiName) => itemApiName !== apiName);

    editField({ value: newOptions });
  };

  const renderField = () => {
    const fieldsMap: { [key in EExtraFieldMode]: React.ReactNode } = {
      [EExtraFieldMode.Kickoff]: renderKickoffField(),
      [EExtraFieldMode.ProcessRun]: renderProcessRunField(),
    };

    return fieldsMap[mode];
  };

  return renderField();
}
