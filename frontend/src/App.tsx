import { useEffect, useState } from "react";

const services = [
  { id: "user", name: "User Service", database: "f168_user" },
  { id: "loan", name: "Loan Service", database: "f168_loan" },
  { id: "payment", name: "Payment Service", database: "f168_payment" },
];

type State = "checking" | "ready" | "down";
const labels = { checking: "Đang kiểm tra", ready: "Sẵn sàng", down: "Chưa sẵn sàng" };

function ServiceRow({ service, revision }: { service: typeof services[number]; revision: number }) {
  const [state, setState] = useState<State>("checking");

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    const timer = window.setTimeout(() => controller.abort(), 8000);

    async function check() {
      setState("checking");
      try {
        const response = await fetch("/health/" + service.id, {
          signal: controller.signal, cache: "no-store",
        });
        if (!response.ok) throw new Error("health");
        const data = await response.json();
        const ready = data.service === service.id && data.status === "ok" && data.database === "ok";
        if (active) setState(ready ? "ready" : "down");
      } catch {
        if (active) setState("down");
      } finally {
        window.clearTimeout(timer);
      }
    }
    void check();
    return () => {
      active = false;
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [service.id, revision]);

  return (
    <li className="service-row">
      <div><h3>{service.name}</h3><code>{service.database}</code></div>
      <span className={"status " + state} role="status"><i />{labels[state]}</span>
      <a className="doc-link" href={"/docs/" + service.id} aria-label={"Mở Swagger " + service.name}>Swagger <span aria-hidden="true">↗</span></a>
    </li>
  );
}

export default function App() {
  const [revision, setRevision] = useState(0);
  return (
    <>
      <header><div className="container-line"><strong>F168</strong><span className="brand-detail">Loan Installment</span></div></header>
      <main>
        <h1>Trạng thái hệ thống</h1>
        <p className="intro">Kiểm tra kết nối giữa Gateway, từng dịch vụ FastAPI và cơ sở dữ liệu PostgreSQL tương ứng.</p>
        <section aria-labelledby="services-title">
          <div className="section-head flex flex-wrap items-center justify-between gap-3">
            <h2 id="services-title">Dịch vụ</h2>
            <button type="button" onClick={() => setRevision(revision + 1)}>Kiểm tra lại</button>
          </div>
          <ul>{services.map(service => <ServiceRow key={service.id} service={service} revision={revision} />)}</ul>
        </section>
      </main>
    </>
  );
}
