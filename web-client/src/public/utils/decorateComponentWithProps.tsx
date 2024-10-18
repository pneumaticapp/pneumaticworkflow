import React, { Component, ComponentType } from 'react';

const getDisplayName = (WrappedComponent: ComponentType) => (
  WrappedComponent.displayName || WrappedComponent.name || 'Component'
);

export const decorateComponentWithProps = (EmbeddedComponent: React.ComponentType<{}>  , props: any) => {
  return (
    class extends Component {
      static displayName = `Decorated(${getDisplayName(EmbeddedComponent)})`;
    
      render() {
        return (
          <EmbeddedComponent {...this.props} {...props} />
        );
      }
    }
  )
};
