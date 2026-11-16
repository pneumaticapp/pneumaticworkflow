import * as React from 'react';
import { useIntl } from 'react-intl';
import { Link } from 'react-router-dom';

import { history } from '../../../../utils/history';
import { getTemplateEditRoute } from '../../../../utils/routes';

import { Tooltip } from '../../../UI';
import { DropdownList } from '../../../UI/DropdownList';

import { TFieldsetUsageBannerProps } from './types';

import styles from './FieldsetUsageBanner.css';

export const FieldsetUsageBanner = ({ usage }: TFieldsetUsageBannerProps) => {
  const { formatMessage } = useIntl();
  const isLinked = usage.length > 0;

  if (isLinked) {
    return (
      <div className={`${styles['usage-banner']} ${styles['usage-banner--linked']}`}>
        <div className={styles['usage-banner__row']}>
          <span>
            {formatMessage({ id: 'fieldsets.usage.linked' }, { count: usage.length })}
          </span>
          <DropdownList
            controlSize="sm"
            className={styles['usage-banner__dropdown']}
            title={formatMessage({ id: 'fieldsets.usage.show' })}
            options={usage.map((template) => ({
              value: template.name,
              onClick: () => {
                history.push(getTemplateEditRoute(template.id));
              },
              label: (
                <Tooltip
                  content={template.name}
                  placement="top"
                  interactive={false}
                  appendTo={() => document.body}
                  containerClassName={styles['usage-banner__option-tooltip']}
                  contentClassName={styles['usage-banner__tooltip-content']}
                >
                  <Link
                    to={getTemplateEditRoute(template.id)}
                    className={styles['usage-banner__link']}
                  >
                    {template.name}
                  </Link>
                </Tooltip>
              ),
            }))}
            filterOption={(option, inputValue) =>
              (option.data as { value: string }).value?.toLowerCase().includes(inputValue.toLowerCase()) ?? true
            }
            placement="left"
            classNames={{
              menuList: () => styles['usage-banner__menu-list'],
              option: () => styles['usage-banner__option'],
            }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className={`${styles['usage-banner']} ${styles['usage-banner--not-linked']}`}>
      {formatMessage({ id: 'fieldsets.usage.not-linked' })}
    </div>
  );
};
