import React from 'react';

export const ShortArrowIcon = ({ fill = 'currentColor' }: React.SVGAttributes<SVGElement>) => {
  return (
    <svg width="8" height="6" viewBox="0 0 8 6" fill={fill} xmlns="http://www.w3.org/2000/svg">
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        // eslint-disable-next-line max-len
        d="M7.83286 0.618279C8.06782 0.999824 8.05422 1.46608 7.79733 1.836L5.13066 5.436C4.88701 5.78686 4.45972 6 4 6C3.54028 6 3.11299 5.78686 2.86934 5.436L0.20267 1.836C-0.0542207 1.46608 -0.0678239 0.999823 0.167144 0.618277C0.402111 0.236732 0.848633 -1.90682e-08 1.33333 0H6.66667C7.15137 1.90682e-08 7.59789 0.236733 7.83286 0.618279Z"
        fill={fill}
      />
    </svg>
  );
};
