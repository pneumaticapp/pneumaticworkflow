import * as React from 'react';
import { useMemo, useRef } from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import TextareaAutosize from 'react-textarea-autosize';

import { Tooltip, FilterSelect } from '../../../UI';
import { FilledInfoIcon } from '../../../icons';
import { EFieldLabelPosition } from '../../../../types/fieldset';
import { FIELDSET_LABEL_POSITION_OPTIONS } from '../../constants';

import { TFieldsetSettingsProps } from './types';

import fieldsetDetailsStyles from '../FieldsetDetails.css';
import styles from './FieldsetSettings.css';

export const FieldsetSettings = ({
  title,
  description,
  labelPosition,
  isReadOnly,
  isTitleError,
  onTitleChange,
  onDescriptionChange,
  onLabelPositionChange,
}: TFieldsetSettingsProps) => {
  const { formatMessage } = useIntl();
  const labelPositionRef = useRef<HTMLDivElement>(null);

  const labelPositionOptions = useMemo(
    () =>
      FIELDSET_LABEL_POSITION_OPTIONS.map((option) => ({
        id: option.value,
        name: formatMessage({ id: option.labelKey }),
      })),
    [formatMessage],
  );

  return (
    <div className={fieldsetDetailsStyles['list']}>
      <h2 className={fieldsetDetailsStyles['section-title']}>
        {formatMessage({ id: 'fieldsets.settings-section' })}
        {isReadOnly && (
          <span className={fieldsetDetailsStyles['readonly-badge']}>
            {formatMessage({ id: 'fieldsets.readonly-badge' })}
          </span>
        )}
      </h2>

      <div className={styles['settings-form']}>
        <div className={styles['settings-field']}>
          <label htmlFor="fieldset-title" className={styles['settings-label']}>
            {formatMessage({ id: 'fieldsets.settings.title' })}
            <Tooltip
              content={formatMessage({ id: 'fieldsets.settings.title-tooltip' })}
              placement="top"
            >
              <span>
                <FilledInfoIcon />
              </span>
            </Tooltip>
          </label>
          {isReadOnly ? (
            <TextareaAutosize
              id="fieldset-title"
              minRows={1}
              className={styles['settings-title']}
              value={title}
              disabled
            />
          ) : (
            <input
              id="fieldset-title"
              type="text"
              className={classnames(
                styles['settings-title'],
                isTitleError && styles['settings-title_error'],
              )}
              value={title}
              placeholder={formatMessage({ id: 'fieldsets.settings.title-placeholder' })}
              onChange={onTitleChange}
            />
          )}
        </div>

        <div className={styles['settings-field']}>
          <label htmlFor="fieldset-description" className={styles['settings-label']}>
            {formatMessage({ id: 'fieldsets.settings.description' })}
            <Tooltip
              content={formatMessage({ id: 'fieldsets.settings.description-tooltip' })}
              placement="top"
            >
              <span className={styles['settings-info-icon']}>
                <FilledInfoIcon />
              </span>
            </Tooltip>
          </label>
          {isReadOnly ? (
            <TextareaAutosize
              id="fieldset-description"
              minRows={3}
              className={styles['settings-description']}
              value={description}
              disabled
            />
          ) : (
            <textarea
              id="fieldset-description"
              className={styles['settings-description']}
              value={description}
              placeholder={formatMessage({ id: 'fieldsets.settings.description-placeholder' })}
              onChange={onDescriptionChange}
            />
          )}
        </div>

        <div className={styles['settings-field']}>
          <span
            role="button"
            tabIndex={0}
            className={styles['settings-label']}
            onClick={() => labelPositionRef.current?.querySelector<HTMLButtonElement>('button')?.focus()}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                labelPositionRef.current?.querySelector<HTMLButtonElement>('button')?.focus();
              }
            }}
          >
            {formatMessage({ id: 'fieldsets.settings.label-position' })}
          </span>
          <div ref={labelPositionRef}>
            <FilterSelect<'id', 'name', { id: EFieldLabelPosition; name: string }>
              optionIdKey="id"
              optionLabelKey="name"
              options={labelPositionOptions}
              selectedOption={labelPosition}
              onChange={(key) => {
                if (key && key !== labelPosition) {
                  onLabelPositionChange(key as EFieldLabelPosition);
                }
              }}
              resetFilter={() => { }}
              placeholderText=""
              isDisabled={isReadOnly}
              containerClassname={fieldsetDetailsStyles['settings-select']}
              toggleClassName={fieldsetDetailsStyles['settings-select__toggle']}
              menuClassName={fieldsetDetailsStyles['settings-select__menu']}
              renderPlaceholder={() => labelPositionOptions.find((option) => option.id === labelPosition)?.name || ''}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
