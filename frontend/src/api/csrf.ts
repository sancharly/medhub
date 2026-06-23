export function withCsrf(headers: HeadersInit): Headers {
  const result = new Headers(headers);
  const match = document.cookie
    .split("; ")
    .find((row) => row.startsWith("csrftoken="));
  if (match) {
    result.set("X-CSRF-Token", match.slice("csrftoken=".length));
  }
  return result;
}
