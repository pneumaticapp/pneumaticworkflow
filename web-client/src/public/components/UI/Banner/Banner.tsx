import React from 'react';

import { Button } from "../Buttons/Button";

import styles from './Banner.css';

export function Banner({ lsKey, text, buttonText, link }: IBannerProps) {
  if (localStorage.getItem(lsKey)) {
    return null;
  }

  const handleClick = () => {
    localStorage.setItem(lsKey, String(true));
  };

  return (
    <div className={styles['banner']}>
      <p className={styles['banner__text']}>{text}</p>
      <Button
        className={styles['banner__btn']}
        wrapper="a"
        href={link}
        target="_blank"
        onClick={handleClick}
        buttonStyle="yellow"
        label={buttonText}
      />
    </div>
  );
}

interface IBannerProps {
  lsKey: string;
  text: string;
  link: string;
  buttonText: string;
}
