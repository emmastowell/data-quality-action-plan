import { Routes, Route, Link } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import AssetsList from "./pages/AssetsList";
import AssetDetail from "./pages/AssetDetail";
import ExportPage from "./pages/ExportPage";

export default function App() {
  return (
    <>
      <header className="govuk-header" role="banner">
        <div
          className="govuk-header__container govuk-width-container"
          style={{ paddingTop: "30px", paddingBottom: "30px", borderBottom: "10px solid #1d70b8" }}
        >
          <span
            className="govuk-header__logotype-text"
            style={{ fontSize: "2.5rem", lineHeight: 1.1, fontWeight: 700 }}
          >
            Data Quality Action Plans
          </span>
        </div>
      </header>
      <div className="govuk-width-container">
        <div className="govuk-phase-banner">
          <p className="govuk-phase-banner__content">
            <strong className="govuk-tag govuk-phase-banner__content__tag">Beta</strong>
            <span className="govuk-phase-banner__text">
              An accelerator implementing the GOV.UK data quality action plan methodology.
            </span>
          </p>
        </div>
        <nav className="govuk-!-margin-top-3">
          <Link className="govuk-link" to="/">Dashboard</Link>{" · "}
          <Link className="govuk-link" to="/assets">Data assets</Link>
        </nav>
        <main className="govuk-main-wrapper" id="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/assets" element={<AssetsList />} />
            <Route path="/assets/:id" element={<AssetDetail />} />
            <Route path="/assets/:id/export" element={<ExportPage />} />
          </Routes>
        </main>
      </div>
      <footer className="govuk-footer">
        <div className="govuk-width-container">
          <div className="govuk-footer__meta">
            <div className="govuk-footer__meta-item govuk-footer__meta-item--grow">
              <span className="govuk-footer__licence-description">
                Built with the{" "}
                <a className="govuk-footer__link" href="https://design-system.service.gov.uk/" rel="noreferrer" target="_blank">
                  GOV.UK Design System
                </a>
              </span>
            </div>
          </div>
        </div>
      </footer>
    </>
  );
}
