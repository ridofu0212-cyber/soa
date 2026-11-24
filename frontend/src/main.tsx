import { createRoot } from "react-dom/client";
import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import App from "./App";
import "./styles.css";

createRoot(document.getElementById("root")!).render(
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<App />} />
      <Route path="*" element={<main><h1>Không tìm thấy trang</h1><Link to="/">Trạng thái hệ thống</Link></main>} />
    </Routes>
  </BrowserRouter>,
);
