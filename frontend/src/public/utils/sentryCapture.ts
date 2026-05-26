type CaptureExceptionFn = (error: Error) => void;

let captureExceptionImpl: CaptureExceptionFn = () => {};

export const setSentryCapture = (fn: CaptureExceptionFn): void => {
  captureExceptionImpl = fn;
};

export const captureException = (error: Error): void => {
  captureExceptionImpl(error);
};
