import { redirect } from "next/navigation";

// Settings live on the profile screen in the demo (language + log out).
export default function SettingsPage() {
  redirect("/profile");
}
