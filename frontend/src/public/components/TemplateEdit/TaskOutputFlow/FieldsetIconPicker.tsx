import * as React from 'react';
import { useCallback, useMemo, useRef } from 'react';
import { useIntl } from 'react-intl';
import { useSelector } from 'react-redux';
import classNames from 'classnames';

import { IFieldsetCatalogItem } from '../../../types/fieldset';
import { getFieldsetsCatalogItems } from '../../../redux/selectors/fieldsets';
import { CustomTooltip } from '../../UI/CustomTooltip';
import { Dropdown, type TDropdownOption } from '../../UI';
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
  selectedFieldsetIds: number[];
  onSelectFieldset: (fieldsetCatalogItem: IFieldsetCatalogItem) => void;
  onRemoveFieldset: (sharedFieldsetId: number) => void;
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
  selectedFieldsetIds,
  onSelectFieldset,
  onRemoveFieldset,
}: IFieldsetIconPickerProps) => {
  const { formatMessage } = useIntl();
  const triggerRef = useRef<HTMLSpanElement>(null);
  const fieldsetsCatalogItems = useSelector(getFieldsetsCatalogItems);

  const catalogRows = useMemo(() => buildCatalogPickerRows(fieldsetsCatalogItems), [fieldsetsCatalogItems]);
  const showListLoading = fieldsetsCatalogLoading && catalogRows.length === 0;

  const handleToggleFieldset = useCallback(
    (sharedFieldsetId: number) => {
      if (selectedFieldsetIds.includes(sharedFieldsetId)) {
        onRemoveFieldset(sharedFieldsetId);
        return;
      }
      const fieldsetCatalogItem = fieldsetsCatalogItems.find((item) => item.id === sharedFieldsetId);
      if (fieldsetCatalogItem) {
        onSelectFieldset(fieldsetCatalogItem);
      }
    },
    [fieldsetsCatalogItems, onRemoveFieldset, onSelectFieldset, selectedFieldsetIds],
  );

  const catalogDropdownOption = useMemo((): TDropdownOption => {
    return {
      mapKey: 'template.fieldset-icon-picker.catalog',
      label: '\u00a0',
      customSubOption: (
        <div className={flowStyles['flow__fieldset-dropdown-panel']}>
          {showListLoading ? (
            <div className={pickerStyles['fieldset-picker__loading']}>
              {formatMessage({ id: 'template.fieldset-picker.loading', defaultMessage: 'Loading…' })}
            </div>
          ) : null}

          {!showListLoading && catalogRows.length === 0 ? (
            <div className={pickerStyles['fieldset-picker__empty']}>
              {formatMessage({ id: 'template.fieldset-picker.empty' })}
            </div>
          ) : null}

          {!showListLoading
            && catalogRows.map((row) => {
              const isSelected = selectedFieldsetIds.includes(row.id);
              return (
                <button
                  key={row.id}
                  type="button"
                  className={pickerStyles['fieldset-picker__option']}
                  onClick={() => handleToggleFieldset(row.id)}
                  id={`task-output-fieldset-option-${row.id}`}
                >
                  <input
                    type="checkbox"
                    className={pickerStyles['fieldset-picker__checkbox']}
                    checked={isSelected}
                    readOnly
                    tabIndex={-1}
                    aria-hidden
                  />
                  <div className={pickerStyles['fieldset-picker__option-info']}>
                    <span className={pickerStyles['fieldset-picker__option-name']}>{row.name}</span>
                    <span className={pickerStyles['fieldset-picker__option-meta']}>
                      {row.fieldsCount} fields · {row.rulesCount} rules
                    </span>
                  </div>
                </button>
              );
            })}
        </div>
      ),
    };
  }, [
    catalogRows,
    formatMessage,
    handleToggleFieldset,
    selectedFieldsetIds,
    showListLoading,
  ]);

  return (
    <div className={flowStyles['flow__fieldset-icon-slot']}>
      <Dropdown
        direction="left"
        menuPositionFixed
        toggleProps={{id: 'task-output-fieldset-icon'}}
        renderToggle={(isOpen) => (
          <span
            ref={triggerRef}
            className={classNames(kickoffStyles['component-icon-container'], isOpen && flowStyles['flow__fieldset-icon-trigger_open'])}
          >
            <FieldsetIcon className={kickoffStyles['component-icon']} aria-hidden />
          </span>
        )}
        options={catalogDropdownOption}
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
