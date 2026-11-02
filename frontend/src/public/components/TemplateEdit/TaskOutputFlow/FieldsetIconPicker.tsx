import * as React from 'react';
import { useCallback, useMemo, useRef } from 'react';
import { useIntl } from 'react-intl';
import { useSelector } from 'react-redux';

import { IFieldsetCatalogItem } from '../../../types/fieldset';
import { getFieldsetsCatalogItems } from '../../../redux/selectors/fieldsets';
import { CustomTooltip } from '../../UI/CustomTooltip';
import { Tooltip } from '../../UI/Tooltip';
import { Select, TSelectOption } from '../../UI/Select';
import { FieldsetIcon } from '../../icons/FieldsetIcon';

import pickerStyles from './FieldsetIconPicker.css';
import kickoffStyles from '../KickoffRedux/KickoffRedux.css';
import flowStyles from '../OutputForm/OutputForm.css';

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

export const FieldsetIconPicker = ({ fieldsetsCatalogLoading, onSelectFieldset }: IFieldsetIconPickerProps) => {
  const { formatMessage } = useIntl();
  const triggerRef = useRef<HTMLSpanElement>(null);
  const fieldsetsCatalogItems = useSelector(getFieldsetsCatalogItems);

  const options = useMemo((): TSelectOption[] => {
    const rows = buildCatalogPickerRows(fieldsetsCatalogItems);
    return rows.map((row) => ({
      value: String(row.id),
      searchByText: row.name,
      label: (
        <Tooltip
          content={row.name}
          placement="top"
          interactive={false}
          appendTo={() => document.body}
          contentClassName={pickerStyles['fieldset-picker__tooltip-content']}
        >
          <div className={pickerStyles['fieldset-picker__option-info']}>
            <span className={pickerStyles['fieldset-picker__option-name']}>{row.name}</span>
            <span className={pickerStyles['fieldset-picker__option-meta']}>
              {row.fieldsCount} fields · {row.rulesCount} rules
            </span>
          </div>
        </Tooltip>
      ),
    }));
  }, [fieldsetsCatalogItems]);

  const handleSelectFieldset = useCallback(
    ({ value }: TSelectOption) => {
      const fieldsetCatalogItem = fieldsetsCatalogItems.find((item) => String(item.id) === value);
      if (fieldsetCatalogItem) {
        onSelectFieldset(fieldsetCatalogItem);
      }
    },
    [fieldsetsCatalogItems, onSelectFieldset],
  );

  return (
    <div className={flowStyles['flow__fieldset-icon-slot']}>
      <Select
        controlSize="sm"
        isSearchable
        options={options}
        value={null}
        isLoading={fieldsetsCatalogLoading && options.length === 0}
        onChange={handleSelectFieldset}
        placeholder={formatMessage({ id: 'search.placeholder', defaultMessage: 'Search...' })}
        noOptionsMessage={() => formatMessage({ id: 'template.fieldset-picker.empty' })}
        menuPortalTarget={document.body}
        menuPosition="fixed"
        controlContent={
          <span ref={triggerRef} className={kickoffStyles['component-icon-container']}>
            <FieldsetIcon className={kickoffStyles['component-icon']} aria-hidden />
          </span>
        }
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
