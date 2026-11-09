const setDefaultDirection = (element: Element, direction: 'auto' | 'ltr' | 'rtl'): void => {
  if (!element.hasAttribute('dir')) {
    element.setAttribute('dir', direction);
  }
};

/** Decorate rendered content only; the original Markdown and its list ordering stay unchanged. */
export const setRichTextDirection = (content: DocumentFragment): void => {
  const prose = content.querySelectorAll('p, h1, h2, h3, h4, h5, h6');
  const firstListBlocks = new Map<Element, Element>();

  prose.forEach((element) => {
    const listItem = element.closest('li');
    if (listItem && !firstListBlocks.has(listItem)) {
      firstListBlocks.set(listItem, element);
    }
  });

  content.querySelectorAll('li').forEach((element) => {
    const authoredDirection = firstListBlocks.get(element)?.getAttribute('dir');
    setDefaultDirection(element, authoredDirection === 'rtl' || authoredDirection === 'ltr' ? authoredDirection : 'auto');
  });

  content.querySelectorAll('td, th, dt, dd').forEach((element) => {
    setDefaultDirection(element, 'auto');
  });

  prose.forEach((element) => {
    const listItem = element.closest('li');
    const firstListBlock = listItem && firstListBlocks.get(listItem);

    // Native auto direction ignores descendants with their own dir. The first prose block
    // must inherit its li so its text determines the marker side as well as the prose.
    if (element !== firstListBlock) {
      setDefaultDirection(element, 'auto');
    }
  });

  content.querySelectorAll('pre, code').forEach((element) => {
    setDefaultDirection(element, 'ltr');
  });
};
