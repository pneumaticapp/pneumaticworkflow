import * as React from 'react';
import { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react';

import { scrollToElement } from '../../../utils/helpers';
import { TTaskFormPart } from '../types';
import { getValidationErrorMap } from './collectTemplateValidationErrors';
import { TTemplateValidationError } from './types';

type TTaskFocusRequest = {
  taskUuid: string;
  formPart: TTaskFormPart;
};

interface ITemplateValidationContextValue {
  isValidationVisible: boolean;
  errorsByPath: Record<string, string>;
  blockingErrors: TTemplateValidationError[];
  revealBlockingErrors(errors: TTemplateValidationError[]): void;
  getError(path: string): string | undefined;
  hasErrorMatching(prefix: string): boolean;
  consumeTaskFocusRequest(taskUuid: string): TTaskFormPart | null;
  consumeExpandKickoffRequest(): boolean;
  clearValidation(): void;
}

const TemplateValidationContext = createContext<ITemplateValidationContextValue | null>(null);

const SCROLL_RETRY_DELAYS_MS = [0, 100, 300, 600];

function scrollToValidationAnchor(path: string) {
  const anchor = document.querySelector(`[data-template-validation-anchor="${path}"]`);
  if (anchor instanceof HTMLElement) {
    scrollToElement(anchor);
    return true;
  }

  return false;
}

function scheduleScrollToAnchor(path: string) {
  SCROLL_RETRY_DELAYS_MS.forEach((delay) => {
    window.setTimeout(() => {
      scrollToValidationAnchor(path);
    }, delay);
  });
}

interface ITemplateValidationProviderProps {
  openTask(taskUuid?: string): void;
  children: React.ReactNode;
}

export function TemplateValidationProvider({ openTask, children }: ITemplateValidationProviderProps) {
  const [isValidationVisible, setIsValidationVisible] = useState(false);
  const [blockingErrors, setBlockingErrors] = useState<TTemplateValidationError[]>([]);
  const [errorsByPath, setErrorsByPath] = useState<Record<string, string>>({});
  const taskFocusRequestRef = useRef<TTaskFocusRequest | null>(null);
  const expandKickoffRequestRef = useRef(false);

  const focusScrollTarget = useCallback((error: TTemplateValidationError) => {
    const { scrollTarget, path } = error;

    if (scrollTarget.area === 'name' || scrollTarget.area === 'owners' || scrollTarget.area === 'tasks') {
      scheduleScrollToAnchor(scrollTarget.area);
      return;
    }

    if (scrollTarget.area === 'kickoff') {
      expandKickoffRequestRef.current = true;
      scheduleScrollToAnchor(path);
      if (!scrollToValidationAnchor(path)) {
        scheduleScrollToAnchor('kickoff');
      }
      return;
    }

    if (scrollTarget.area === 'task') {
      openTask(scrollTarget.taskUuid);
      taskFocusRequestRef.current = {
        taskUuid: scrollTarget.taskUuid,
        formPart: scrollTarget.formPart,
      };
      scheduleScrollToAnchor(path);
    }
  }, [openTask]);

  const revealBlockingErrors = useCallback((errors: TTemplateValidationError[]) => {
    const nextMap = getValidationErrorMap(errors);

    setBlockingErrors(errors);
    setErrorsByPath(nextMap);
    setIsValidationVisible(errors.length > 0);

    if (errors.length > 0) {
      focusScrollTarget(errors[0]);
    }
  }, [focusScrollTarget]);

  const clearValidation = useCallback(() => {
    setIsValidationVisible(false);
    setBlockingErrors([]);
    setErrorsByPath({});
    taskFocusRequestRef.current = null;
    expandKickoffRequestRef.current = false;
  }, []);

  const consumeTaskFocusRequest = useCallback((taskUuid: string) => {
    const request = taskFocusRequestRef.current;
    if (!request || request.taskUuid !== taskUuid) {
      return null;
    }

    taskFocusRequestRef.current = null;
    return request.formPart;
  }, []);

  const consumeExpandKickoffRequest = useCallback(() => {
    if (!expandKickoffRequestRef.current) {
      return false;
    }

    expandKickoffRequestRef.current = false;
    return true;
  }, []);

  const getError = useCallback((path: string) => errorsByPath[path], [errorsByPath]);

  const hasErrorMatching = useCallback(
    (prefix: string) => Object.keys(errorsByPath).some((path) => path === prefix || path.startsWith(`${prefix}.`)),
    [errorsByPath],
  );

  const value = useMemo<ITemplateValidationContextValue>(
    () => ({
      isValidationVisible,
      errorsByPath,
      blockingErrors,
      revealBlockingErrors,
      getError,
      hasErrorMatching,
      consumeTaskFocusRequest,
      consumeExpandKickoffRequest,
      clearValidation,
    }),
    [
      isValidationVisible,
      errorsByPath,
      blockingErrors,
      revealBlockingErrors,
      getError,
      hasErrorMatching,
      consumeTaskFocusRequest,
      consumeExpandKickoffRequest,
      clearValidation,
    ],
  );

  return <TemplateValidationContext.Provider value={value}>{children}</TemplateValidationContext.Provider>;
}

export function useTemplateValidation(): ITemplateValidationContextValue {
  const ctx = useContext(TemplateValidationContext);

  if (!ctx) {
    throw new Error('useTemplateValidation must be used inside TemplateValidationProvider');
  }

  return ctx;
}

export function useTemplateValidationOptional(): ITemplateValidationContextValue | null {
  return useContext(TemplateValidationContext);
}
