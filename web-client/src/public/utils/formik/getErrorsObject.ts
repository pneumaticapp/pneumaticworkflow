export function getErrorsObject<Fields>(
  values: Fields,
  errorsMap: { [key in keyof Partial<Fields>]: (value: any) => string },
): { [key in keyof Partial<Fields>]: string } {
  const errors = Object.keys(errorsMap).reduce((acc, item) => {
    const fieldName = item as keyof Partial<Fields>;
    const fieldError = errorsMap[fieldName]?.(values[fieldName]);

    return fieldError ? { ...acc, [fieldName]: fieldError } : acc;
  }, {} as { [key in keyof Partial<Fields>]: string });

  return errors;
}
