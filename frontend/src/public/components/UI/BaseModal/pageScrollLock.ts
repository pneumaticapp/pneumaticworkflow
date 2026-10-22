let activeLocksCount = 0;

export const lockPageScroll = () => {
  activeLocksCount += 1;
  document.body.style.overflow = 'hidden';
};

export const unlockPageScroll = () => {
  activeLocksCount = Math.max(0, activeLocksCount - 1);
  if (activeLocksCount === 0) {
    document.body.style.overflow = '';
  }
};
