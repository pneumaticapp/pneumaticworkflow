import * as React from 'react';
import { ReactNode, useCallback, useMemo, useRef } from 'react';
import { useIntl } from 'react-intl';
import { useSelector } from 'react-redux';

import { IFieldsetCatalogItem } from '../../../types/fieldset';
import { getFieldsetsCatalogItems } from '../../../redux/selectors/fieldsets';
import { CustomTooltip } from '../../UI/CustomTooltip';
import { FilterSelect } from '../../UI';
import { FieldsetIcon } from '../../icons/FieldsetIcon';

import pickerStyles from './FieldsetIconPicker.css';
import kickoffStyles from '../KickoffRedux/KickoffRedux.css';
import flowStyles from '../OutputForm/OutputForm.css';

interface IFieldsetCatalogOption {
  id: number;
  name: string;
  label: ReactNode;
  searchByText: string;
}

interface IFieldsetCatalogPickerRow {
  id: number;
  apiName: string;
  name: string;
  fieldsCount: number;
  rulesCount: number;
  order: number;
}

export interface IFieldsetIconPickerProps {
  fieldsetsCatalogLoading: boolean;
  onSelectFieldset: (fieldsetCatalogItem: IFieldsetCatalogItem) => void;
}

const buildCatalogPickerRows = (catalogFieldsetItems: IFieldsetCatalogItem[]): IFieldsetCatalogPickerRow[] => {
  const rows = catalogFieldsetItems.map<IFieldsetCatalogPickerRow>((catalogFieldsetItem) => ({
    id: catalogFieldsetItem.id,
    apiName: catalogFieldsetItem.apiName,
    name: catalogFieldsetItem.name,
    fieldsCount: catalogFieldsetItem.fields.length,
    rulesCount: catalogFieldsetItem.rules.length,
    order: catalogFieldsetItem.order,
  }));
  rows.sort((a, b) => {
    if (a.order !== b.order) {
      return a.order - b.order;
    }
    return a.name.localeCompare(b.name);
  });
  return rows;
};

export const FieldsetIconPicker = ({
  fieldsetsCatalogLoading,
  onSelectFieldset,
}: IFieldsetIconPickerProps) => {
  const { formatMessage } = useIntl();
  const triggerRef = useRef<HTMLSpanElement>(null);
  const fieldsetsCatalogItems = useSelector(getFieldsetsCatalogItems);

  const options = useMemo((): IFieldsetCatalogOption[] => {
    const rows = buildCatalogPickerRows(fieldsetsCatalogItems);
    return rows.map((row) => ({
      id: row.id,
      name: row.name,
      searchByText: row.name,
      label: (
        <div className={pickerStyles['fieldset-picker__option-info']}>
          <span className={pickerStyles['fieldset-picker__option-name']}>{row.name}</span>
          <span className={pickerStyles['fieldset-picker__option-meta']}>
            {row.fieldsCount} fields · {row.rulesCount} rules
          </span>
        </div>
      ),
    }));
  }, [fieldsetsCatalogItems]);

  const handleSelectFieldset = useCallback(
    (sharedFieldsetId: number | null) => {
      if (sharedFieldsetId === null) return;
      const fieldsetCatalogItem = fieldsetsCatalogItems.find((item) => item.id === sharedFieldsetId);
      if (fieldsetCatalogItem) {
        onSelectFieldset(fieldsetCatalogItem);
      }
    },
    [fieldsetsCatalogItems, onSelectFieldset],
  );

  return (
    <div className={flowStyles['flow__fieldset-icon-slot']}>
      <FilterSelect<'id', 'label', IFieldsetCatalogOption>
        optionIdKey="id"
        optionLabelKey="label"
        options={options}
        isLoading={fieldsetsCatalogLoading}
        isSearchShown
        positionFixed
        selectedOption={null}
        onChange={handleSelectFieldset}
        resetFilter={() => {}}
        searchPlaceholder={formatMessage({ id: 'search.placeholder', defaultMessage: 'Search...' })}
        placeholderText={formatMessage({ id: 'template.fieldset-picker.empty' })}
        containerClassname={pickerStyles['fieldset-picker__container']}
        toggleClassName={pickerStyles['fieldset-picker__toggle']}
        menuClassName={pickerStyles['fieldset-picker__menu']}
        arrowClassName={pickerStyles['fieldset-picker__arrow_hidden']}
        renderPlaceholder={() => (
          <span
            ref={triggerRef}
            className={kickoffStyles['component-icon-container']}
          >
            <FieldsetIcon className={kickoffStyles['component-icon']} aria-hidden />
          </span>
        )}
      />
      <CustomTooltip
        target={triggerRef}
        tooltipText={formatMessage({
          id: 'template.task-output-fieldset-icon-help',
          defaultMessage: 'Click to choose a fieldset for this step',
        })}
        tooltipTitle={formatMessage({ id: 'fieldsets.title' })}
      />
    </div>
  );
};

