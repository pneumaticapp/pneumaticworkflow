export function escapeMarkdown(text: string = ''): string {
  const variables: string[] = [];
  text = text.replace(/{{([^{}]+)}}/g, (match) => {
    variables.push(match);
    return `__VAR_${variables.length - 1}__`;
  });

  text = text.replace(/([\\`*_[\]{}()#+\-.!|&%=:"'~])/g, '\\$1');
  variables.forEach((variable, index) => {
    text = text.replace(`\\_\\_VAR\\_${index}\\_\\_`, variable);
  });

  return text;
}
