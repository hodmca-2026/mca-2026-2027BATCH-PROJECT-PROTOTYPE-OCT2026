// FastAPI returns `detail` as a string for HTTP errors but as a list for validation errors.
export function errMsg(err, fallback) {
  const d = err?.response?.data?.detail;
  return typeof d === "string" ? d : fallback;
}
