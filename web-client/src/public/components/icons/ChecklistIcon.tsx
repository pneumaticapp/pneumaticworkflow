import React from "react";

export function ChecklistIcon({ fill = 'currentColor' }: React.SVGAttributes<SVGElement>) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill={fill} xmlns="http://www.w3.org/2000/svg">
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M5 3H19C20.1 3 21 3.9 21 5V19C21 20.1 20.1 21 19 21H5C3.9 21 3 20.1 3 19L3.01 5C3.01 3.9 3.9 3 5 3ZM5 19H19V5H5V19Z"
      />
      <path fillRule="evenodd" clipRule="evenodd" d="M11 13.17L15.59 8.57999L17 9.99999L11 16L7 12L8.41 10.59L11 13.17Z" />
    </svg>
  );
}
