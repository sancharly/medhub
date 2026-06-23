// Client-side convenience checks only. Server is authoritative for all policy.
export const passwordHints = {
  checkLength: (password: string): boolean => password.length >= 12,
  checkClasses: (password: string): boolean => {
    const hasUpper = /[A-Z]/.test(password);
    const hasLower = /[a-z]/.test(password);
    const hasDigit = /[0-9]/.test(password);
    const hasSpecial = /[^A-Za-z0-9]/.test(password);
    return hasUpper && hasLower && hasDigit && hasSpecial;
  },
  checkSubstring: (password: string, context: string): boolean =>
    context.length === 0 || !password.toLowerCase().includes(context.toLowerCase()),
};
