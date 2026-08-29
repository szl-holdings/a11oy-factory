export type OpenPr = {
  disposition: string;
  number: number;
  reason: string;
  repository: string;
  source_url: string;
  title: string;
};

export type FactoryCounts = {
  a11oy_routes_in_audit: number;
  a11oy_spaces_route_displayed: number;
  github_archived: number;
  github_private: number;
  github_public: number;
  github_public_page_displayed: number;
  github_repositories_authenticated: number;
  hf_assets_in_audit: number;
  hf_buckets: number;
  hf_collections: number;
  hf_datasets: number;
  hf_kernels: number;
  hf_models_dedicated_listing: number;
  hf_models_org_front: number;
  hf_spaces: number;
  killinchu_routes_in_audit: number;
  open_prs_authenticated: number;
  vertical_cells: number;
};

export type VerticalCell = {
  vertical_id: string;
};

export type FormulaBinding = {
  formula_id: string;
};

export type FactoryProfile = {
  counts: FactoryCounts;
  current_open_prs: OpenPr[];
  formula_bindings: FormulaBinding[];
  vertical_cells: VerticalCell[];
};
