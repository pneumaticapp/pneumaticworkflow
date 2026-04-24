/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import classnames from 'classnames';

import { DropdownList } from '../../../UI/DropdownList';

import { getEmptySelection } from '../../KickoffRedux/utils/getEmptySelection';
import { fitInputWidth } from '../utils/fitInputWidth';
import { getInputNameBackground } from '../utils/getInputNameBackground';
import { RemoveIcon, ArrowDropdownIcon } from '../../../icons';
import { IntlMessages } from '../../../IntlMessages';
import { FieldWithName } from '../utils/FieldWithName';
import { DatasetSourceToggle } from '../utils/DatasetSourceToggle';
import { getFieldValidator } from '../utils/getFieldValidator';
import { EExtraFieldMode, IExtraFieldSelection } from '../../../../types/template';
import { validateCheckboxAndRadioField } from '../../../../utils/validators';
import { handleSelectionBlur, recalculateDuplicateErrors } from '../utils/handleSelectionBlur';

import { IWorkflowExtraFieldProps } from '..';

import styles from '../../KickoffRedux/KickoffRedux.css';
import inputStyles from './ExtraFieldCreatable.css';

const DEFAULT_OPTION_INPUT_WIDTH = 120;

export interface IDropdownSelection {
  value: string;
  label: string;
}

/*
  TODO: Rename all {Creatable} to {Dropdown}
  Details: https://trello.com/c/RqrYD3lc/1154-extrafields-rename
*/

export function ExtraFieldCreatable({
  field,
  intl,
  descriptionPlaceholder = intl.formatMessage({ id: 'template.kick-off-form-field-description-placeholder' }),
  namePlaceholder = intl.formatMessage({ id: 'template.kick-off-form-field-name-placeholder' }),
  mode = EExtraFieldMode.Kickoff,
  editField,
  deleteField,
  isDisabled = false,
  labelBackgroundColor,
  innerRef,
  datasetName,
}: IWorkflowExtraFieldProps) {
  const { isRequired } = field;
  const optionInputsRefs = React.useRef<HTMLInputElement[]>([]);

  React.useEffect(() => {
    optionInputsRefs.current.forEach((input) => fitInputWidth(input, DEFAULT_OPTION_INPUT_WIDTH));
  }, [field.selections]);

  const { useCallback, useState, useMemo } = React;

  const { description } = field;
  const selectionItems = field.selections as IExtraFieldSelection[];
  const selectionValues = field.selections as string[];

  const dropdownSelections: IDropdownSelection[] = useMemo(
    () => (selectionValues || []).map((selectionValue) => ({
      value: selectionValue,
      label: selectionValue,
    } as IDropdownSelection)),
    [selectionValues],
  );

  const [activeOptionIndex, setActiveOptionIndex] = useState<number | null>(null);
  const [duplicateErrors, setDuplicateErrors] = useState<Record<string, string>>(
    () => recalculateDuplicateErrors(selectionItems || []),
  );

  const handleSelectableChange = (inputValue: IDropdownSelection) => {
    editField({ value: inputValue.value });
  };

  const fieldNameClassName = classnames(getInputNameBackground(labelBackgroundColor), styles['kick-off-input__name']);

  const handleChangeName = useCallback(
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      editField({ name: e.target.value });
    },
    [editField],
  );

  const handleChangeDescription = useCallback(
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      editField({ description: e.target.value });
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

  const renderKickoffOption = ({ value, apiName }: IExtraFieldSelection, optionIndex: number) => {
    const isActive = optionIndex === activeOptionIndex;
    const standardError = validateCheckboxAndRadioField(value);
    const errorMessageIntl = standardError || duplicateErrors[apiName] || '';
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
            ref={(el) => (optionInputsRefs.current[optionIndex] = el as HTMLInputElement)}
            className={inputStyles['kickoff-create-field-option__input']}
            onChange={handleChangeOption(optionIndex)}
            onBlur={handleBlurOption(apiName)}
            placeholder={namePlaceholder}
            type="text"
            value={value}
            disabled={isDisabled}
          />
          <span className={inputStyles['measure']} />
          {isActive && !isDisabled && (selectionItems?.length || 0) > 1 && (
            <div
              role="button"
              className={inputStyles['kickoff-create-field-option__remove']}
              onClick={handleRemoveOption(optionIndex)}
            >
              <RemoveIcon />
            </div>
          )}
        </div>
        {shouldShowError && (
          <p className={inputStyles['kickoff-create-field__error-text']}>
            <IntlMessages id={errorMessageIntl} />
          </p>
        )}
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

  const renderKickoffView = () => {
    const customOptionsList = selectionItems && (
      <ul className={inputStyles['kickoff-create-field-options']}>{selectionItems?.map(renderKickoffOption)}</ul>
    );

    const addOptionButton = (
      <button type="button" className={inputStyles['kickoff-create-field-add-option']} onClick={handleAddOption}>
        <IntlMessages id="template.kick-off-add-options" />
      </button>
    );

    return (
      <div className={inputStyles['kickoff-create-field-container']}>
        {renderKickoffField()}

        <DatasetSourceToggle field={field} editField={editField} isDisabled={isDisabled} datasetName={datasetName}>
          {customOptionsList}
          {!isDisabled && addOptionButton}
        </DatasetSourceToggle>
      </div>
    );
  };

  const renderSelectableView = () => {
    const displayValue = dropdownSelections.find((selection) => selection.value === field.value) || null;

    return (
      <div className={inputStyles['dropdown-container']} data-autofocus-first-field={true}>
        <div className={fieldNameClassName}>
          <div className={styles['kick-off-input__name-readonly']}>{field.name}</div>
          {isRequired && <span className={styles['kick-off-required-sign']} />}
        </div>
        <DropdownList
          options={dropdownSelections}
          onChange={handleSelectableChange}
          placeholder={description}
          isDisabled={isDisabled}
          isSearchable={false}
          value={displayValue}
        />
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
