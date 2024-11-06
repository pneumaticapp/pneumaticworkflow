import React, { useState } from 'react';
import classNames from 'classnames';

import { ClearIcon } from '../../icons';

import styles from './TemplateSystemCategoryItem.css';

export interface ITemplateSystemCategoryItemProps {
  id: number;
  name: string;
  icon: string;
  color: string;
  isActive: boolean;
  onActiveCategory(id: number): void;
}

export function TemplateSystemCategoryItem({
  id,
  name,
  color,
  icon,
  isActive,
  onActiveCategory,
}: ITemplateSystemCategoryItemProps) {
  const [isHover, setIsHover] = useState(false);

  const handleMouseEnter = () => {
    setIsHover(true);
  };

  const handleMouseLeave = () => {
    setIsHover(false);
  };

  const activeHoverStyle = {
    color: !isHover ? 'white' : color,
    borderColor: color,
    background: !isHover ? color : 'transparent',
  };

  const hoverStyle = {
    color: !isHover ? color : 'white',
    borderColor: !isHover ? color : 'white',
    background: !isHover ? 'transparent' : color,
  };

  return (
    <button
      style={!isActive ? hoverStyle : activeHoverStyle}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className={classNames(styles['categories'])}
      key={id}
      onClick={() => (!isActive ? onActiveCategory(id) : onActiveCategory(0))}
      type="button"
    >
      <div className={styles['categories__icon']}>{!isActive ? <img src={icon} alt={name} /> : <ClearIcon />}</div>
      <span>{name}</span>
    </button>
  );
}
