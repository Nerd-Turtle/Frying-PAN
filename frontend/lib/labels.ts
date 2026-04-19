export function formatUserRole(role: string) {
  switch (role.trim().toLowerCase()) {
    case "admin":
      return "Administrator";
    case "operator":
      return "Operator";
    default:
      return role;
  }
}
