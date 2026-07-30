import React, { FormEvent, useEffect, useState } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { removeAiConnection, saveAiConnection } from '../../../redux/actions';
import { getAiConnectionState } from '../../../redux/selectors/aiAgents';
import { Button, InputField } from '../../UI';

import styles from './AiConnection.css';

export function AiConnection() {
  const dispatch = useDispatch();
  const { formatMessage } = useIntl();
  const { isAvailable, isSaving, value } = useSelector(getAiConnectionState);

  const [apiKey, setApiKey] = useState('');
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    setApiKey('');
    setIsEditing(false);
  }, [value?.id]);

  if (!isAvailable) {
    return null;
  }

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    const normalizedKey = apiKey.trim();
    if (!normalizedKey) return;

    dispatch(saveAiConnection({ apiKey: normalizedKey }));
  };

  if (value && !isEditing) {
    return (
      <section className={styles['connection']}>
        <div className={styles['connection__info']}>
          <p className={styles['connection__title']}>{formatMessage({ id: 'ai-agents.connection.title' })}</p>
          <p className={styles['connection__key']}>{value.apiKeyMask}</p>
        </div>
        <div className={styles['connection__buttons']}>
          <Button
            type="button"
            label={formatMessage({ id: 'ai-agents.connection.replace' })}
            buttonStyle="transparent-black"
            size="sm"
            onClick={() => setIsEditing(true)}
          />
          <button
            type="button"
            className="cancel-button"
            disabled={isSaving}
            onClick={() => dispatch(removeAiConnection())}
          >
            {formatMessage({ id: 'ai-agents.connection.remove' })}
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className={styles['connection']}>
      <div className={styles['connection__info']}>
        <p className={styles['connection__title']}>{formatMessage({ id: 'ai-agents.connection.title' })}</p>
        <p className={styles['connection__description']}>
          {formatMessage({ id: 'ai-agents.connection.description' })}
        </p>
        <form onSubmit={handleSubmit} className={styles['connection__form']}>
          <InputField
            value={apiKey}
            onChange={(e) => setApiKey(e.currentTarget.value)}
            fieldSize="md"
            placeholder={formatMessage({ id: 'ai-agents.connection.key-placeholder' })}
            containerClassName={styles['connection__field']}
          />
          <div className={styles['connection__buttons']}>
            <Button
              type="submit"
              label={formatMessage({ id: 'ai-agents.connection.save' })}
              buttonStyle="yellow"
              size="md"
              disabled={isSaving || !apiKey.trim()}
            />
            {value && (
              <button type="button" className="cancel-button" onClick={() => setIsEditing(false)}>
                {formatMessage({ id: 'ai-agents.connection.cancel' })}
              </button>
            )}
          </div>
        </form>
      </div>
    </section>
  );
}
