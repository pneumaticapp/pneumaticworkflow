import React from "react";

export function useWhiteBackground() {
  React.useEffect(() => {
    document.body.style.background = "white";

    return () => {
      document.body.style.background = "unset";
    };
  }, []);
}
