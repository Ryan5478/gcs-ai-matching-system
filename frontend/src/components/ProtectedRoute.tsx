import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { ReactNode } from "react";

type Props = {
  children: ReactNode;
  allowedRoles?: Array<"candidate" | "employer" | "admin">;
};

export default function ProtectedRoute({ children, allowedRoles }: Props) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (allowedRoles && !allowedRoles.includes(user.role)) return <Navigate to="/" replace />;
  return <>{children}</>;
}
