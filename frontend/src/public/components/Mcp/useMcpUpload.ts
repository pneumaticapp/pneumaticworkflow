import * as React from 'react';
import { useFormik } from 'formik';
import { mixed, object } from 'yup';
import { getMcpUploadSession, mcpErrorMessage, uploadMcpFile } from '../../api/mcp';
import { IMcpUploadFormValues, IMcpUploadSession } from '../../types/mcp';
import { canonicalMcpContentType } from '../../utils/mcpFileMetadata';
import { isMcpId } from '../../utils/safeRedirect';

export function useMcpUpload(sessionId: string) {
  const [session, setSession] = React.useState<IMcpUploadSession>();
  const [csrf, setCsrf] = React.useState('');
  const [error, setError] = React.useState('');
  const [busy, setBusy] = React.useState(false);
  const [sent, setSent] = React.useState(false);
  const controller = React.useRef<AbortController>();
  const operating = React.useRef(false);

  const refresh = React.useCallback(
    async (signal: AbortSignal) => {
      try {
        const data = await getMcpUploadSession(sessionId, signal);
        if (signal.aborted) return;
        setSession(data.session);
        setCsrf(data.csrf_token);
        setError('');
      } catch (reason) {
        if (!signal.aborted) {
          const message = mcpErrorMessage(reason);
          setError(message);
          // A transient read failure must preserve the reconciliation action.
          if (message !== 'mcp.error.unavailable') setSession(undefined);
        }
      }
    },
    [sessionId],
  );

  const submit = React.useCallback(
    async (values: IMcpUploadFormValues) => {
      const signal = controller.current?.signal;
      if (
        !values.file ||
        values.sessionId !== sessionId ||
        !session ||
        operating.current ||
        sent ||
        session.status !== 'pending' ||
        !signal ||
        signal.aborted
      )
        return;
      if (Date.parse(session.expires_at) <= Date.now()) {
        setError('mcp.error.expired');
        setSession(undefined);
        return;
      }
      operating.current = true;
      setBusy(true);
      setError('');
      let dispatched = false;
      try {
        await uploadMcpFile(values.file, session, csrf, signal, () => {
          dispatched = true;
          // Once bytes are dispatched, only a session read proves their state.
          if (!signal.aborted) setSent(true);
        });
        if (!signal.aborted) await refresh(signal);
      } catch (reason) {
        if (!signal.aborted) {
          const message = mcpErrorMessage(reason);
          setError(message);
          if (!dispatched && message !== 'mcp.error.unavailable') await refresh(signal);
        }
      } finally {
        if (!signal.aborted) {
          operating.current = false;
          setBusy(false);
        }
      }
    },
    [session, sessionId, sent, csrf, refresh],
  );

  const validationSchema = React.useMemo(
    () =>
      object({
        file: mixed<File>()
          .required('mcp.upload.invalid-file')
          .test('session-file', 'mcp.upload.invalid-file', (file) =>
            Boolean(
              file &&
              session &&
              file.size > 0 &&
              file.size === session.size &&
              (!session.content_type || canonicalMcpContentType(file.type) === session.content_type),
            ),
          ),
      }),
    [session],
  );
  const initialValues = React.useMemo<IMcpUploadFormValues>(() => ({ sessionId, file: undefined }), [sessionId]);
  const form = useFormik<IMcpUploadFormValues>({
    initialValues,
    enableReinitialize: true,
    validateOnChange: false,
    validateOnBlur: false,
    validationSchema,
    onSubmit: submit,
  });
  const { resetForm, setFieldValue, setFieldError } = form;

  React.useEffect(() => {
    const requestController = new AbortController();
    controller.current = requestController;
    operating.current = false;
    setSession(undefined);
    resetForm();
    setError('');
    setSent(false);
    setBusy(false);
    if (!isMcpId(sessionId)) setError('mcp.error.expired');
    else
      getMcpUploadSession(sessionId, requestController.signal)
        .then((data) => {
          if (!requestController.signal.aborted) {
            setSession(data.session);
            setCsrf(data.csrf_token);
          }
        })
        .catch((reason) => {
          if (!requestController.signal.aborted) setError(mcpErrorMessage(reason));
        });
    return () => requestController.abort();
  }, [sessionId, resetForm]);

  const handleRefresh = React.useCallback(async () => {
    const signal = controller.current?.signal;
    if (operating.current || !signal || signal.aborted) return;
    operating.current = true;
    setBusy(true);
    try {
      await refresh(signal);
    } finally {
      if (!signal.aborted) {
        operating.current = false;
        setBusy(false);
      }
    }
  }, [refresh]);
  const handleFileChange = React.useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      void setFieldValue('file', event.currentTarget.files?.item(0) || undefined, false);
      setFieldError('file', undefined);
      setError('');
    },
    [setFieldValue, setFieldError],
  );

  return {
    session,
    error: error || (typeof form.errors.file === 'string' ? form.errors.file : ''),
    busy: busy || form.isSubmitting,
    sent,
    form,
    handleFileChange,
    handleRefresh,
  };
}
