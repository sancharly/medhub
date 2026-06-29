export function withCsrf(headers: HeadersInit): Headers {
  const result = new Headers(headers);
  const match = document.cookie
    .split("; ")
    .find((row) => row.startsWith("medhub_csrf="));
  if (match) {
    result.set("X-CSRF-Token", match.slice("medhub_csrf=".length));
  }
  return result;
}
