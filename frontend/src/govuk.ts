// govuk.ts — import the compiled GOV.UK stylesheet and initialise its JS components.
import "govuk-frontend/dist/govuk/govuk-frontend.min.css";
import { initAll } from "govuk-frontend";
export function initGovuk() {
  document.documentElement.classList.add("govuk-frontend-supported");
  document.body.classList.add("govuk-frontend-supported");
  initAll();
}
