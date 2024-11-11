export function reactElementToText(elem: JSX.Element): any {
  if (!elem) {
    return '';
  }
  if (typeof elem === 'string') {
    return elem;
  }

  const children = elem.props && elem.props.children;
  if (children instanceof Array) {
    return children.map(reactElementToText).join('');
  }
  return reactElementToText(children);
}
