import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ThemeProvider as MuiThemeProvider } from "@mui/material/styles";
import { ConfirmProvider } from "./ConfirmProvider";
import { useConfirm } from "./useConfirm";
import { theme } from "../theme/theme";

function Wrapper({ children }: { children: React.ReactNode }) {
  return (
    <MuiThemeProvider theme={theme}>
      <ConfirmProvider>{children}</ConfirmProvider>
    </MuiThemeProvider>
  );
}

function TestButton({
  options,
  onResult,
}: {
  options: Parameters<ReturnType<typeof useConfirm>>[0];
  onResult: (v: boolean) => void;
}) {
  const confirm = useConfirm();
  return (
    <button
      onClick={async () => {
        const result = await confirm(options);
        onResult(result);
      }}
    >
      open
    </button>
  );
}

describe("ConfirmDialog", () => {
  it("opens dialog on confirm() call", async () => {
    const onResult = vi.fn();
    render(
      <Wrapper>
        <TestButton
          options={{ title: "Delete item", description: "Are you sure?" }}
          onResult={onResult}
        />
      </Wrapper>
    );

    await userEvent.click(screen.getByText("open"));
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("Delete item")).toBeInTheDocument();
  });

  it("Confirm button resolves true", async () => {
    const onResult = vi.fn();
    render(
      <Wrapper>
        <TestButton
          options={{ title: "Delete", description: "Sure?" }}
          onResult={onResult}
        />
      </Wrapper>
    );

    await userEvent.click(screen.getByText("open"));
    await userEvent.click(screen.getByText("Confirm"));

    await waitFor(() => expect(onResult).toHaveBeenCalledWith(true));
  });

  it("Cancel button resolves false", async () => {
    const onResult = vi.fn();
    render(
      <Wrapper>
        <TestButton
          options={{ title: "Delete", description: "Sure?" }}
          onResult={onResult}
        />
      </Wrapper>
    );

    await userEvent.click(screen.getByText("open"));
    await userEvent.click(screen.getByText("Cancel"));

    await waitFor(() => expect(onResult).toHaveBeenCalledWith(false));
  });

  it("Escape key resolves false", async () => {
    const onResult = vi.fn();
    render(
      <Wrapper>
        <TestButton
          options={{ title: "Delete", description: "Sure?" }}
          onResult={onResult}
        />
      </Wrapper>
    );

    await userEvent.click(screen.getByText("open"));
    await userEvent.keyboard("{Escape}");

    await waitFor(() => expect(onResult).toHaveBeenCalledWith(false));
  });

  it("destructive variant uses error color on confirm button", async () => {
    render(
      <Wrapper>
        <TestButton
          options={{ title: "Delete", description: "Sure?", destructive: true }}
          onResult={vi.fn()}
        />
      </Wrapper>
    );

    await userEvent.click(screen.getByText("open"));
    const confirmBtn = screen.getByText("Confirm");
    expect(confirmBtn.closest("button")).toHaveClass("MuiButton-colorError");
  });

  it("destructive variant autofocuses Cancel, not Confirm", async () => {
    render(
      <Wrapper>
        <TestButton
          options={{ title: "Delete", description: "Sure?", destructive: true }}
          onResult={vi.fn()}
        />
      </Wrapper>
    );

    await userEvent.click(screen.getByText("open"));
    // After dialog opens, the Cancel button should receive focus (not Confirm)
    // MUI Dialog moves focus to the autoFocus element; verify via document.activeElement
    const cancelBtn = screen.getByText("Cancel").closest("button");
    const confirmBtn = screen.getByText("Confirm").closest("button");
    expect(document.activeElement).toBe(cancelBtn);
    expect(document.activeElement).not.toBe(confirmBtn);
  });

  it("has accessible labelling", async () => {
    render(
      <Wrapper>
        <TestButton
          options={{ title: "Accessible Dialog", description: "Some description" }}
          onResult={vi.fn()}
        />
      </Wrapper>
    );

    await userEvent.click(screen.getByText("open"));
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("aria-labelledby");
    expect(dialog).toHaveAttribute("aria-describedby");
  });
});
