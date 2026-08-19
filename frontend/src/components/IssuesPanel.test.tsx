import { render, screen, fireEvent } from "@testing-library/react";
import { IssueForm } from "./IssuesPanel";

const BLANK_INITIAL = {
  title: "", description: "", rule_id: "", dimension: "",
  reported_by: "", assigned_to: "", business_area: "", data_subject: "",
  impacted_systems: "", example_reference: "", system_owner: "",
  related_issues: "", comments: "", priority: "medium", severity: "medium",
  likelihood: "medium", impact_tags: [] as string[], root_cause_category: "",
  contributing_factors: "", root_cause_detail: "", status: "open", status_date: "",
};

it("blocks submission and shows error when title is empty", () => {
  const onSubmit = vi.fn();
  render(
    <IssueForm
      initial={BLANK_INITIAL}
      rules={[]}
      onSubmit={onSubmit}
      onCancel={() => {}}
      submitLabel="Log issue"
    />,
  );
  fireEvent.click(screen.getByText("Log issue"));
  expect(onSubmit).not.toHaveBeenCalled();
  expect(screen.getAllByText(/Enter a title for the issue/).length).toBeGreaterThan(0);
});
