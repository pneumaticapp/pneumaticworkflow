import * as React from 'react';
import { useCallback, useMemo, useRef } from 'react';
import { useIntl } from 'react-intl';
import classNames from 'classnames';

import { IFieldsetData } from '../../../types/template';
import { CustomTooltip } from '../../UI/CustomTooltip';
import { Dropdown, type TDropdownOption } from '../../UI';
import { FieldsetIcon } from '../../icons/FieldsetIcon';

import pickerStyles from '../FieldsetPicker/FieldsetPicker.css';
import kickoffStyles from '../KickoffRedux/KickoffRedux.css';
import flowStyles from '../OutputForm/OutputForm.css';

interface IFieldsetCatalogPickerRow {
  id: number;
  apiName: string;
  name: string;
  fieldsCount: number;
  rulesCount: number;
}

export interface IFieldsetIconPickerProps {
  templateId: number | undefined;
  fieldsetsByApiName: ReadonlyMap<string, IFieldsetData>;
  fieldsetsCatalogLoading: boolean;
  selectedFieldsetApiNames: string[];
  onSelectFieldset: (apiName: string) => void;
  onRemoveFieldset: (apiName: string) => void;
}

const isReadyTemplateId = (id: number | undefined): id is number => typeof id === 'number';

const buildCatalogPickerRows = (map: ReadonlyMap<string, IFieldsetData>): IFieldsetCatalogPickerRow[] => {
  const rows = Array.from(map.values()).map<IFieldsetCatalogPickerRow>((d) => ({
    id: d.id,
    apiName: d.apiName,
    name: d.name,
    fieldsCount: d.fields.length,
    rulesCount: d.rulesCount ?? 0,
  }));
  rows.sort((a, b) => {
    const orderA = map.get(a.apiName)?.order ?? 0;
    const orderB = map.get(b.apiName)?.order ?? 0;
    if (orderA !== orderB) {
      return orderA - orderB;
    }
    return a.name.localeCompare(b.name);
  });
  return rows;
};

export const FieldsetIconPicker = ({
  templateId,
  fieldsetsByApiName,
  fieldsetsCatalogLoading,
  selectedFieldsetApiNames,
  onSelectFieldset,
  onRemoveFieldset,
}: IFieldsetIconPickerProps) => {
  const { formatMessage } = useIntl();
  const triggerRef = useRef<HTMLSpanElement>(null);

  const catalogRows = useMemo(() => buildCatalogPickerRows(fieldsetsByApiName), [fieldsetsByApiName]);
  const showListLoading = fieldsetsCatalogLoading && catalogRows.length === 0;

  const handleToggleFieldset = useCallback(
    (apiName: string) => {
      if (selectedFieldsetApiNames.includes(apiName)) {
        onRemoveFieldset(apiName);
        return;
      }
      onSelectFieldset(apiName);
    },
    [onRemoveFieldset, onSelectFieldset, selectedFieldsetApiNames],
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
              const isSelected = selectedFieldsetApiNames.includes(row.apiName);
              return (
                <button
                  key={row.id}
                  type="button"
                  className={pickerStyles['fieldset-picker__option']}
                  onClick={() => handleToggleFieldset(row.apiName)}
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
    selectedFieldsetApiNames,
    showListLoading,
  ]);

  return (
    <div className={flowStyles['flow__fieldset-icon-slot']}>
      <Dropdown
        isDisabled={!isReadyTemplateId(templateId)}
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
