/* eslint-disable */
/* prettier-ignore */
type TSuggestion = {
  name: string;
};

export function getSuggestionByValue<T>(value: string, suggestions: (T & TSuggestion)[]) {
  return suggestions.filter((suggestion) => {
    return !value || suggestion.name.toLowerCase().indexOf(value.toLowerCase()) > -1;
  });
}
