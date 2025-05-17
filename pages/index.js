import { useState } from "react";
import LoginForm from "../components/LoginForm";

export default function Home() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const handleLogin = (username, password) => {
    return new Promise((resolve, reject) => {
      if (
        username === "PIADMIN" &&
        password === process.env.NEXT_PUBLIC_PIADMIN_PWD
      ) {
        setIsLoggedIn(true);
        resolve();
      } else {
        reject();
      }
    });
  };

  if (isLoggedIn) {
    // Redirect eller link til admin-siden
    return (
      <div style={{ padding: "2rem" }}>
        <h1>Du er logget inn!</h1>
        <p>
          Gå til <a href="/admin">Admin siden</a> for å redigere system prompt og
          speak-tekst.
        </p>
      </div>
    );
  }

  return (
    <div>
      <header
        style={{
          display: "flex",
          justifyContent: "flex-end",
          padding: "1rem",
          borderBottom: "1px solid #ddd",
        }}
      >
        <LoginForm onLogin={handleLogin} />
      </header>

      <main
        style={{
          maxWidth: "600px",
          margin: "3rem auto",
          padding: "0 1rem",
          fontFamily:
            "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
          lineHeight: "1.6",
        }}
      >
        <h1>Velkommen til samtalepartneren Liv</h1>
        <p>
          Alle trenger noen å snakke med for å beholde god psykisk helse og humør.
          Liv er her for å lytte og gi deg støtte når du trenger det.
        </p>
      </main>
    </div>
  );
}
