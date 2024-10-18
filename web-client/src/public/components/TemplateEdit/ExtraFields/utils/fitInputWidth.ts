/* eslint-disable */
/* prettier-ignore */
export const fitInputWidth = (element: HTMLInputElement | null, defaultWidth: number) => {
  const FONT_FACTOR = 13;

  if (element) {
    const value = element.value;
    const measure = element.nextElementSibling;

    if (measure) {
      measure.textContent = element.value;

      value ?
        element.style.width = `${measure.scrollWidth + FONT_FACTOR}px` :
        element.style.width = `${defaultWidth}px`;
    }
  }
};
