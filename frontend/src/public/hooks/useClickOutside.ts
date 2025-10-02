import React from 'react';

export const useClickOutside = (ref: React.RefObject<HTMLButtonElement>, callback: () => void) => {
  const handleClick = (e: any) => {
    if (ref.current && !ref.current.contains(e.target)) {
      callback();
    }
  };
  React.useEffect(() => {
    document.addEventListener('click', handleClick);
    return () => {
      document.removeEventListener('click', handleClick);
    };
  });
};
