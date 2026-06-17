import React from "react";
import { createRoot } from "react-dom/client";
import { RunListPage } from "./pages/RunListPage";

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <RunListPage />
  </React.StrictMode>
);
