/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import classnames from 'classnames';
import AutosizeInput from 'react-input-autosize';

import { getEmptySelection } from '../../KickoffRedux/utils/getEmptySelection';
import { validateCheckboxAndRadioField, validateKickoffFieldName } from '../../../../utils/validators';
import { handleSelectionBlur, recalculateDuplicateErrors } from '../utils/handleSelectionBlur';
import { IntlMessages } from '../../../IntlMessages';
import { EExtraFieldMode, IExtraFieldSelection } from '../../../../types/template';
import { fitInputWidth } from '../utils/fitInputWidth';
import { PencilSmallIcon, RemoveIcon } from '../../../icons';
import { RadioButton } from '../../../UI/Fields/RadioButton';
import { OutputFieldContent } from '../utils/OutputFieldContent';

import { IWorkflowExtraFieldProps } from '..';

import styles from '../../KickoffRedux/KickoffRedux.css';
import fieldStyles from './ExtraFieldRadio.css';
import { useState } from 'react';

const DEFAULT_OPTION_INPUT_WIDTH = 120;
const DEFAULT_FIELD_INPUT_WIDTH = 120;

export function ExtraFieldRadio({
  field,
  field: { isRequired = false, name, value: selectedOption },
  intl,
  namePlaceholder = intl.formatMessage({ id: 'template.kick-off-form-field-name-placeholder' }),
  mode = EExtraFieldMode.Kickoff,
  deleteField,
  editField,
  isDisabled = false,
  datasetName,
}: IWorkflowExtraFieldProps) {
  const selectionItems = field.selections as IExtraFieldSelection[];
  const selectionValues = field.selections as string[];
  const fieldNameInputRef = React.useRef<HTMLInputElement | null>(null);
  const optionInputsRefs = React.useRef<HTMLInputElement[]>([]);
  const [isFocused, setIsFocused] = React.useState(false);

  React.useEffect(() => {
    optionInputsRefs.current.forEach((input) => fitInputWidth(input, DEFAULT_OPTION_INPUT_WIDTH));
  }, [selectionItems]);

  React.useEffect(() => {
    fitInputWidth(fieldNameInputRef.current, DEFAULT_FIELD_INPUT_WIDTH);
  }, []);

  const [activeOptionIndex, setActiveOptionIndex] = useState<number | null>(null);
  const [duplicateErrors, setDuplicateErrors] = useState<Record<string, string>>(
    () => recalculateDuplicateErrors(selectionItems || []),
  );

  const fieldNameErrorMessage = validateKickoffFieldName(name) || '';
  const isKickoffFieldNameValid = !Boolean(fieldNameErrorMessage);

  const renderKickoffField = () => {
    const fieldNameClassName = classnames(fieldStyles['kickoff-create-field-name']);

    const customOptionsList = selectionItems && (
      <ul className={fieldStyles['kickoff-create-field-options']}>{selectionItems?.map(renderKickoffOption)}</ul>
    );

    const addOptionButton = (
      <button type="button" className={fieldStyles['kickoff-create-field-add-option']} onClick={handleAddOption}>
        <IntlMessages id="template.kick-off-add-options" />
      </button>
    );

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

        <OutputFieldContent field={field} editField={editField} isDisabled={isDisabled} datasetName={datasetName}>
          {customOptionsList}
          {!isDisabled && addOptionButton}
        </OutputFieldContent>
      </div>
    );
  };

  const renderKickoffOption = (field: IExtraFieldSelection, optionIndex: number) => {
    const { value } = field;

    const isActive = optionIndex === activeOptionIndex;
    const standardError = validateCheckboxAndRadioField(value);
    const errorMessageIntl = standardError || duplicateErrors[field.apiName] || '';
    const shouldShowError = Boolean(errorMessageIntl);

    return (
      <li
        key={optionIndex}
        className={fieldStyles['kickoff-create-field-option']}
        onMouseOver={() => setActiveOptionIndex(optionIndex)}
        onMouseLeave={() => setActiveOptionIndex(null)}
      >
        <div className={fieldStyles['kickoff-create-field-option__labeled-checkbox']}>
          <RadioButton
            checked={false}
            disabled
            id={`extra-field-radio-${optionIndex}`}
            containerClassName={fieldStyles['connected_radio']}
          />
          <input
            ref={(el) => (optionInputsRefs.current[optionIndex] = el as HTMLInputElement)}
            className={fieldStyles['labeled-checkbox__input']}
            onChange={handleChangeOption(optionIndex)}
            onBlur={handleBlurOption(field.apiName)}
            placeholder={namePlaceholder}
            type="text"
            value={value}
            disabled={isDisabled}
          />
          <span className={fieldStyles['measure']} />
          {isActive && !isDisabled && (selectionItems?.length || 0) > 1 && (
            <div
              role="button"
              className={fieldStyles['labeled-checkbox__remove-icon']}
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

  const handleAddOption = () => {
    const newOptions = [...(selectionItems || []), getEmptySelection(selectionItems)];
    editField({ selections: newOptions });
  };

  const handleRemoveOption = (optionIndex: number) => () => {
    const newOptions = selectionItems?.filter((_, index) => index !== optionIndex) || [];
    editField({ selections: newOptions });
    setDuplicateErrors(recalculateDuplicateErrors(newOptions));
  };

  const handleChangeOption = (optionIndex: number) => (event: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = event.target.value;
    const apiName = selectionItems?.[optionIndex]?.apiName;
    if (apiName) {
      setDuplicateErrors((prev) => ({ ...prev, [apiName]: '' }));
    }

    const newOptions = selectionItems?.map((option, index) => {
      if (index === optionIndex) {
        return { ...option, value: newValue };
      }

      return option;
    });

    editField({ selections: newOptions });
  };

  const handleBlurOption = handleSelectionBlur(setDuplicateErrors, selectionItems);

  const renderProcessRunOption = (selectionValue: string) => {
    const isChecked = selectionValue === selectedOption;

    return (
      <li key={selectionValue} className={fieldStyles['kickoff-set-field-option']}>
        <RadioButton id={selectionValue} title={selectionValue} onChange={handleToggleOption(selectionValue)} checked={isChecked} />
      </li>
    );
  };

  const renderProcessRunField = () => {
    if (!selectionValues) return null;

    const fieldNameClassName = classnames(fieldStyles['kickoff-set-field-name']);

    return (
      <div className={fieldStyles['kickoff-set-field-container']} data-autofocus-first-field={true}>
        <div>
          <div className={fieldNameClassName}>{name}</div>
          {isRequired && <span className={styles['kick-off-required-sign']} />}
        </div>

        <ul className={fieldStyles['kickoff-set-field-options']}>{selectionValues.map(renderProcessRunOption)}</ul>
      </div>
    );
  };

  const handleToggleOption = (selectionValue: string) => () => {
    const isSameValue = selectionValue === selectedOption;
    const valueToSet = isSameValue ? null : selectionValue;

    editField({ value: valueToSet });
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
