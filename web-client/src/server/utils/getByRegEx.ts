export const getByRegEx = (str: string | void, regExStr: RegExp, fallback: string = '') => {
  if (!str) {
    return fallback;
  }
  const result = regExStr.exec(str);

  return (result && result.slice(-1)[0]) || fallback;
};
