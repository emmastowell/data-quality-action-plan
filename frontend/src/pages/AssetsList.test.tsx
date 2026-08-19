import { render, screen, fireEvent } from "@testing-library/react";
import AssetForm from "../components/AssetForm";

it("shows an error when name is empty", () => {
  const onSubmit = vi.fn();
  render(<AssetForm onSubmit={onSubmit} />);
  fireEvent.click(screen.getByText("Save"));
  expect(onSubmit).not.toHaveBeenCalled();
  expect(screen.getByText(/Enter a name/)).toBeInTheDocument();
});
