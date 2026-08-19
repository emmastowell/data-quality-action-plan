import { render, screen, fireEvent } from "@testing-library/react";
import { ActionForm } from "./ActionsPanel";

const BLANK_INITIAL = {
  title: "", description: "", issue_id: "", remediation_type: "",
  assignee_email: "", priority: "medium",
  start_date: "", due_date: "", review_date: "", completed_date: "",
  success_criteria: "", notes: "", status: "todo",
};

it("blocks submission and shows error when title is empty", () => {
  const onSubmit = vi.fn();
  render(
    <ActionForm
      initial={BLANK_INITIAL}
      issues={[]}
      onSubmit={onSubmit}
      onCancel={() => {}}
      submitLabel="Add action"
    />,
  );
  fireEvent.click(screen.getByText("Add action"));
  expect(onSubmit).not.toHaveBeenCalled();
  expect(screen.getAllByText(/Enter a title for the action/).length).toBeGreaterThan(0);
});
