import * as React from 'react';
import { Provider } from 'react-redux';
import ReactDOMServer from 'react-dom/server';

import { store } from '../redux/store';

export function reactElementToText(element: JSX.Element) {
  if (typeof element === 'string') {
    return element;
  }

  const htmlMarkup = ReactDOMServer.renderToStaticMarkup(<Provider store={store}>{element}</Provider>);

  return removeTags(htmlMarkup);
}

function removeTags(str: string) {
  if (!str) {
    return '';
  }

  return str.replace(/(<([^>]+)>)/gi, '');
}
