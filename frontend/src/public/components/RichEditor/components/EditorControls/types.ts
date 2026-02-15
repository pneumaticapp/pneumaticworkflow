export interface IEditorControlsProps {
    onSubmit?: () => void;
    onCancel?: () => void;
    handleSubmit: () => void;
    handleCancel: () => void;
    shouldSubmitAfterFileLoaded: boolean;
    submitIcon?: React.ReactNode;
    cancelIcon?: React.ReactNode;
  }