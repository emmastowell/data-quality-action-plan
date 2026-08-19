// Type shim for govuk-frontend which ships no bundled .d.ts files.
declare module "govuk-frontend" {
  export function initAll(config?: object): void;
  export function createAll(componentClass: unknown, config?: object, scope?: Document | Element): void;
}
