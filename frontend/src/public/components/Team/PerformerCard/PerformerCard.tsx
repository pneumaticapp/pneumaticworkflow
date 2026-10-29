import React from 'react';
import classnames from 'classnames';
import Switch from 'rc-switch';

import { DropdownMenu, Header } from '../../UI';
import { MoreIcon } from '../../icons';
import type { IPerformerCardProps } from './types';

import styles from './PerformerCard.css';

export function PerformerCard({
  avatar,
  name,
  nameBadge,
  description,
  badge,
  toggle,
  options,
  'data-testid': testId,
}: IPerformerCardProps) {
  const renderAside = () => {
    if (badge) {
      return <p className={styles['performer-card__badge']}>{badge}</p>;
    }

    return (
      <>
        {toggle && (
          <div className={styles['performer-card__toggle']}>
            <span>{toggle.label}</span>
            <Switch
              className="custom-switch custom-switch-primary custom-switch-small"
              checked={toggle.isChecked}
              disabled={toggle.isDisabled}
              onChange={toggle.onChange}
              checkedChildren={null}
              unCheckedChildren={null}
              data-testid={testId && `${testId}-toggle`}
            />
          </div>
        )}
        {options && (
          <DropdownMenu
            toggleProps={testId ? { 'data-testid': `${testId}-more` } : undefined}
            renderToggle={(isOpen) => (
              <MoreIcon
                className={classnames(styles['performer-card__more'], isOpen && styles['performer-card__more_active'])}
              />
            )}
            options={options}
          />
        )}
      </>
    );
  };

  return (
    <article className={styles['performer-card']} data-testid={testId}>
      <div className={styles['performer-card__avatar']}>{avatar}</div>
      <div className={styles['performer-card__info']}>
        <Header size="6" tag="h3" className={styles['performer-card__name']}>
          <span className={styles['performer-card__name-text']}>{name}</span>
          {nameBadge && <span className={styles['performer-card__name-badge']}>{nameBadge}</span>}
        </Header>
        {description && <p className={styles['performer-card__description']}>{description}</p>}
      </div>
      <div className={styles['performer-card__aside']}>{renderAside()}</div>
    </article>
  );
}
