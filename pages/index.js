import { useRouter } from "next/router";

export default function Home() {
  const router = useRouter();

  const handleClick = () => {
    router.push("/admin");
  };

  return (
    <div style={{ fontFamily: "sans-serif", lineHeight: "1.6", display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      {/* Del 1 */}
      <section
        style={{
          display: "flex",
          flexDirection: "row",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "2rem",
          background: "linear-gradient(to right, #d9f99d, #fef08a)",
          borderBottomLeftRadius: "2rem",
          borderBottomRightRadius: "2rem",
        }}
      >
        <div>
          <h1 style={{ fontSize: "3rem", fontWeight: "bold", marginBottom: "0.5rem" }}>Liv</h1>
          <h2 style={{ fontSize: "1.5rem", fontWeight: "600" }}>En samtalepartner for alle</h2>
          <p style={{ marginTop: "1rem" }}>
            Liv er en enkel boks som gir selskap og støtte, hvis du trenger noen å snakke med. Den er kunnskapsrik og kan tilpasses ditt behov.
          </p>
          <button
            onClick={handleClick}
            style={{
              marginTop: "1.5rem",
              padding: "0.75rem 1.5rem",
              backgroundColor: "#2563eb",
              color: "white",
              border: "none",
              borderRadius: "0.75rem",
              fontSize: "1rem",
              cursor: "pointer",
            }}
          >
            Logg inn
          </button>
        </div>
        <img
          src="/boksen.png"
          alt="Liv boks"
          style={{
            maxHeight: "350px",
            width: "auto",
            marginLeft: "2rem",
            marginTop: "1rem",
          }}
        />
      </section>

      {/* Spacer for innhold hvis ønskelig */}
      <div style={{ flex: "1" }} />

      {/* Footer */}
      <footer style={{ padding: "1rem", textAlign: "center", backgroundColor: "#f3f4f6" }}>
        <p style={{ fontSize: "0.875rem", color: "#4b5563" }}>
          © {new Date().getFullYear()} <a href="https://www.dmz.no" target="_blank" rel="noopener noreferrer" style={{ color: "#2563eb", textDecoration: "none" }}>DMZ DATA AS</a>. Alle rettigheter reservert.
        </p>
      </footer>
    </div>
  );
}
