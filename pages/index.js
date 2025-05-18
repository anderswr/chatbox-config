import { useRouter } from "next/router";

export default function Home() {
  const router = useRouter();

  const handleClick = () => {
    router.push("/admin");
  };

  return (
    <div style={{ fontFamily: "sans-serif", lineHeight: "1.6" }}>
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
          <h2 style={{ fontSize: "1.5rem", fontWeight: "600" }}>En samtale-partner for alle</h2>
          <p style={{ marginTop: "1rem" }}>
            Liv er en enkel boks som gir selskap og støtte
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
          style={{ maxWidth: "250px", height: "auto", marginLeft: "2rem" }}
        />
      </section>
    </div>
  );
}
