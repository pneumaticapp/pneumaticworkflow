import * as React from 'react';
import { useEffect, useRef, useState } from 'react';
import { useIntl } from 'react-intl';

import { getFieldsets } from '../../../api/fieldsets/getFieldsets';
import { IFieldsetListItem } from '../../../types/fieldset';

import styles from './FieldsetPicker.css';

export interface IFieldsetPickerProps {
  selectedFieldsetIds: number[];
  onChange: (fieldsetIds: number[]) => void;
}

export function FieldsetPicker({ selectedFieldsetIds, onChange }: IFieldsetPickerProps) {
  const { formatMessage } = useIntl();
  const [isOpen, setIsOpen] = useState(false);
  const [fieldsets, setFieldsets] = useState<IFieldsetListItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const abortCtrl = new AbortController();

    setIsLoading(true);
    getFieldsets({ limit: 1000, signal: abortCtrl.signal })
      .then((response) => {
        setFieldsets(response.results);
      })
      .catch(() => {
        // silently ignore aborted requests
      })
      .finally(() => {
        setIsLoading(false);
      });

    return () => abortCtrl.abort();
  }, []);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleToggle = (id: number) => {
    const isSelected = selectedFieldsetIds.includes(id);
    if (isSelected) {
      onChange(selectedFieldsetIds.filter((fId) => fId !== id));
    } else {
      onChange([...selectedFieldsetIds, id]);
    }
  };

  const handleRemove = (id: number) => {
    onChange(selectedFieldsetIds.filter((fId) => fId !== id));
  };

  const selectedFieldsets = fieldsets.filter((fs) => selectedFieldsetIds.includes(fs.id));
  const toggleLabel = selectedFieldsetIds.length
    ? `${selectedFieldsetIds.length} selected`
    : formatMessage({ id: 'template.fieldset-picker.placeholder' });

  return (
    <div className={styles['fieldset-picker']} ref={wrapperRef}>
      <div className={styles['fieldset-picker__dropdown-wrapper']}>
        <button
          type="button"
          className={`${styles['fieldset-picker__toggle']} ${isOpen ? styles['fieldset-picker__toggle_open'] : ''}`}
          onClick={() => setIsOpen(!isOpen)}
          id="fieldset-picker-toggle"
        >
          <span>{toggleLabel}</span>
          <span
            className={`${styles['fieldset-picker__toggle-arrow']} ${isOpen ? styles['fieldset-picker__toggle-arrow_open'] : ''}`}
          >
            ▾
          </span>
        </button>

        {isOpen && (
          <div className={styles['fieldset-picker__dropdown']}>
            {isLoading && (
              <div className={styles['fieldset-picker__loading']}>Loading...</div>
            )}

            {!isLoading && fieldsets.length === 0 && (
              <div className={styles['fieldset-picker__empty']}>
                {formatMessage({ id: 'template.fieldset-picker.empty' })}
              </div>
            )}

            {!isLoading && fieldsets.map((fs) => (
              <button
                key={fs.id}
                type="button"
                className={styles['fieldset-picker__option']}
                onClick={() => handleToggle(fs.id)}
                id={`fieldset-picker-option-${fs.id}`}
              >
                <input
                  type="checkbox"
                  className={styles['fieldset-picker__checkbox']}
                  checked={selectedFieldsetIds.includes(fs.id)}
                  readOnly
                  tabIndex={-1}
                />
                <div className={styles['fieldset-picker__option-info']}>
                  <span className={styles['fieldset-picker__option-name']}>{fs.name}</span>
                  <span className={styles['fieldset-picker__option-meta']}>
                    {fs.fields.length} fields · {fs.rules.length} rules
                  </span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {selectedFieldsets.length > 0 && (
        <div className={styles['fieldset-picker__tags']}>
          {selectedFieldsets.map((fs) => (
            <span key={fs.id} className={styles['fieldset-picker__tag']}>
              {fs.name}
              <button
                type="button"
                className={styles['fieldset-picker__tag-remove']}
                onClick={() => handleRemove(fs.id)}
                aria-label={`Remove ${fs.name}`}
                id={`fieldset-picker-remove-${fs.id}`}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
