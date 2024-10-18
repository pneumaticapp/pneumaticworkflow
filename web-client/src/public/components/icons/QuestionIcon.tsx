/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export const enum QuestionIconSize {
  Small = 'sm',
  Medium = 'md',
}

export interface IQuestionIconProps extends React.SVGAttributes<SVGElement> {
  background?: string;
  size?: QuestionIconSize;
}

export function QuestionIcon({
  fill= '#FEC336',
  background = 'currentColor',
  size = QuestionIconSize.Medium,
  // tslint:disable-next-line: trailing-comma
  ...rest
}: IQuestionIconProps) {
  if (size === QuestionIconSize.Small) {
    return (
      <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" {...rest}>
        <circle cx="16" cy="16" r="16" fill="#E79A26"/>
        <path d="M16 21L15 20V19H17V20L16 21Z" fill={fill}/>
        <path d="M18.3 15.69C18.3 15.69 17.92 16.11 17.63 16.4C17.15 16.88 16.8 17.55 16.8 18H15.2C15.2 17.17 15.66 16.48 16.13 16L17.06 15.06C17.33 14.79 17.5 14.41 17.5 14C17.5 13.17 16.83 12.5 16 12.5C15.17 12.5 14.5 13.17 14.5 14H13C13 12.34 14.34 11 16 11C17.66 11 19 12.34 19 14C19 14.66 18.73 15.26 18.3 15.69Z" fill="#FEC336" />
      </svg>
    );
  }

  return (
    <svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg" {...rest}>
      <circle cx="20" cy="20" r="20" fill={background}/>
      <path d="M20 25L19 24V23H21V24L20 25Z" fill={fill}/>
      <path d="M22.3 19.69C22.3 19.69 21.92 20.11 21.63 20.4C21.15 20.88 20.8 21.55 20.8 22H19.2C19.2 21.17 19.66 20.48 20.13 20L21.06 19.06C21.33 18.79 21.5 18.41 21.5 18C21.5 17.17 20.83 16.5 20 16.5C19.17 16.5 18.5 17.17 18.5 18H17C17 16.34 18.34 15 20 15C21.66 15 23 16.34 23 18C23 18.66 22.73 19.26 22.3 19.69Z" fill="#FEC336" />
    </svg>
  );
}
