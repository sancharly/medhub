import { Component } from "react";
import type { ReactNode, ErrorInfo } from "react";
import Button from "@mui/material/Button";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class AppErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(_error: Error, _info: ErrorInfo) {
    // Errors logged by monitoring tooling; not exposed to users
  }

  reset() {
    this.setState({ hasError: false, error: null });
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box
          role="alert"
          sx={{ p: 3, textAlign: "center" }}
          data-testid="error-fallback"
        >
          <Typography variant="h6" gutterBottom>
            Something went wrong
          </Typography>
          <Button variant="contained" onClick={() => this.reset()}>
            Try again
          </Button>
        </Box>
      );
    }

    return this.props.children;
  }
}
