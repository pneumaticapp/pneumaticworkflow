/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import classnames from 'classnames';
import AutosizeInput from 'react-input-autosize';

import { DropdownList } from '../../../UI/DropdownList';

import { getEmptySelection } from '../../KickoffRedux/utils/getEmptySelection';
import { fitInputWidth } from '../utils/fitInputWidth';
import { getInputNameBackground } from '../utils/getInputNameBackground';
import { RemoveIcon, ArrowDropdownIcon } from '../../../icons';
import { isArrayWithItems } from '../../../../utils/helpers';
import { IntlMessages } from '../../../IntlMessages';
import { FieldWithName } from '../utils/FieldWithName';
import { getFieldValidator } from '../utils/getFieldValidator';
import {
  EExtraFieldMode,
  IExtraFieldSelection,
} from '../../../../types/template';
import { validateCheckboxAndRadioField } from '../../../../utils/validators';

import { IWorkflowExtraFieldProps } from '..';

import styles from '../../KickoffRedux/KickoffRedux.css';
import inputStyles from './ExtraFieldCreatable.css';

const DEFAULT_OPTION_INPUT_WIDTH = 120;
const DEFAULT_FIELD_INPUT_WIDTH = 120;

export interface IDropdownSelection extends IExtraFieldSelection {
  label: string;
}

/*
  TODO: Rename all {Creatable} to {Dropdown}
  Details: https://trello.com/c/RqrYD3lc/1154-extrafields-rename
*/

export function ExtraFieldCreatable({
  field,
  field: {
    isRequired,
  },
  intl,
  descriptionPlaceholder = intl.formatMessage({ id: 'template.kick-off-form-field-description-placeholder' }),
  namePlaceholder = intl.formatMessage({ id: 'template.kick-off-form-field-name-placeholder' }),
  mode = EExtraFieldMode.Kickoff,
  editField,
  deleteField,
  isDisabled = false,
  labelBackgroundColor,
  innerRef,
}: IWorkflowExtraFieldProps) {
  const fieldNameInputRef = React.useRef<HTMLInputElement | null>(null);
  const optionInputsRefs = React.useRef<HTMLInputElement[]>([]);

  React.useEffect(() => {
    optionInputsRefs.current.forEach(input => fitInputWidth(input, DEFAULT_OPTION_INPUT_WIDTH));
  }, [field.selections]);

  React.useEffect(() => {
    fitInputWidth(fieldNameInputRef.current, DEFAULT_FIELD_INPUT_WIDTH);
  }, []);

  const { useCallback, useState, useMemo } = React;

  const { selections, description } = field;

  const dropdownSelections: IDropdownSelection[] = useMemo(() => (selections || [])
    .map(selection => ({ ...selection, label: selection.value })), [selections]);

  const [activeOptionIndex, setActiveOptionIndex] = useState<number | null>(null);

  const handleSelectableChange = (inputValue: IDropdownSelection) => {
    editField({
      value: String(inputValue.id),
      selections: selections?.map(selection => ({ ...selection, isSelected: inputValue.id === selection.id })),
    });
  };

  const fieldNameClassName =
    classnames(
      getInputNameBackground(labelBackgroundColor),
      styles['kick-off-input__name'],
    );

  const handleChangeName = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    fitInputWidth(e.target, DEFAULT_FIELD_INPUT_WIDTH);
    editField({ name: e.target.value });
  }, [editField]);

  const handleDeleteField = useCallback(() => {
    if (!deleteField) {
      return;
    }

    deleteField();
  }, [deleteField]);

  const handleChangeDescription = useCallback((e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    editField({ description: e.target.value });
  }, [editField]);

  const handleAddOption = () => {
    const newOptions = [...selections as IExtraFieldSelection[], getEmptySelection()];
    editField({ selections: newOptions });
  };

  const handleRemoveOption = (optionIndex: number) => () => {
    const newOptions = selections?.filter((_, index) => index !== optionIndex);

    const isNoOptions = !isArrayWithItems(newOptions);

    isNoOptions
      ? handleDeleteField()
      : editField({ selections: newOptions });
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

  const renderKickoffOption = ({ value, id }: IExtraFieldSelection, optionIndex: number) => {
    const isActive = optionIndex === activeOptionIndex;
    const errorMessageIntl = validateCheckboxAndRadioField(value);
    const shouldShowError = Boolean(errorMessageIntl);

    return (
      <li
        key={optionIndex}
        className={inputStyles['kickoff-create-field-option']}
        onMouseOver={() => setActiveOptionIndex(optionIndex)}
        onMouseLeave={() => setActiveOptionIndex(null)}
      >
        <div className={inputStyles['kickoff-create-field__input-container']}>
          <input
            ref={el => optionInputsRefs.current[optionIndex] = el as HTMLInputElement}
            className={inputStyles['kickoff-create-field-option__input']}
            onChange={handleChangeOption(optionIndex)}
            placeholder={namePlaceholder}
            type="text"
            value={value}
            disabled={isDisabled}
          />
          <span className={inputStyles['measure']} />
          {isActive && !isDisabled && (
            <div
              role="button"
              className={inputStyles['kickoff-create-field-option__remove']}
              onClick={handleRemoveOption(optionIndex)}
            >
              <RemoveIcon />
            </div>
          )}
        </div>
        {shouldShowError &&
          <p className={inputStyles['kickoff-create-field__error-text']}>
            <IntlMessages id={errorMessageIntl} />
          </p>
        }
      </li>
    );
  };

  const renderKickoffField = () => (
    <FieldWithName
      inputClassName={inputStyles['kickoff-dropdown-field']}
      labelBackgroundColor={labelBackgroundColor}
      field={field}
      descriptionPlaceholder={descriptionPlaceholder}
      namePlaceholder={namePlaceholder}
      mode={mode}
      handleChangeName={handleChangeName}
      handleChangeDescription={handleChangeDescription}
      validate={getFieldValidator(field, mode)}
      isDisabled={isDisabled}
      icon={<ArrowDropdownIcon />}
      innerRef={innerRef}
    />
  );

  const renderKickoffView = () => (
    <div className={inputStyles['kickoff-create-field-container']}>
      {renderKickoffField()}

      {selections && (
        <ul className={inputStyles['kickoff-create-field-options']}>
          {selections?.map(renderKickoffOption)}
        </ul>
      )}

      {!isDisabled && (
        <button
          type="button"
          className={inputStyles['kickoff-create-field-add-option']}
          onClick={handleAddOption}
        >
          <IntlMessages id="template.kick-off-add-options" />
        </button>
      )}
    </div>
  );

  const renderSelectableView = () => {
    const displayValue = {
      label: field.selections
        ?.find(selection => Number(selection.id) === Number(field.value))
        ?.value,
    };

    return (
      <div
        className={classnames('has-float-label', inputStyles['dropdown-container'])}
        data-autofocus-first-field={true}
      >
        <DropdownList
          options={dropdownSelections}
          onChange={handleSelectableChange}
          placeholder={description}
          isDisabled={isDisabled}
          isSearchable={false}
          value={displayValue}
        />
        <div className={fieldNameClassName}>
          <AutosizeInput
            inputRef={ref => fieldNameInputRef.current = ref}
            inputClassName={inputStyles['kickoff-create-field-name-input']}
            disabled={mode !== EExtraFieldMode.Kickoff || isDisabled}
            onChange={handleChangeName}
            placeholder={namePlaceholder}
            type="text"
            value={field.name}
          />
          {isRequired && <span className={styles['kick-off-required-sign']} />}
        </div>
      </div>
    );
  };

  const renderDropdownField = () => {
    const fieldsMap: { [key in EExtraFieldMode]: React.ReactNode } = {
      [EExtraFieldMode.Kickoff]: renderKickoffView(),
      [EExtraFieldMode.ProcessRun]: renderSelectableView(),
    };

    return fieldsMap[mode];
  };

  return renderDropdownField();
}
