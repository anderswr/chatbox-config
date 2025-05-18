import React from "react";
import { createRoot } from "react-dom/client";
import "./index.css";

const App = () => {
  const handleLogin = () => {
    window.location.href = "/admin";
  };

  return (
    <div className="min-h-screen flex flex-col bg-white text-black">
      {/* Del 1: Toppen */}
      <section className="flex flex-col md:flex-row justify-between items-start md:items-center p-8 bg-gradient-to-br from-green-100 to-yellow-100 rounded-b-3xl shadow">
        <div className="max-w-xl">
          <h1 className="text-5xl font-bold mb-2">Liv</h1>
          <h2 className="text-2xl font-semibold">En samtale-partner for alle</h2>
          <p className="mt-4 text-lg">Liv er en enkel boks som gir selskap og støtte</p>
          <button
            onClick={handleLogin}
            className="mt-6 px-6 py-3 bg-blue-600 text-white rounded-xl text-lg hover:bg-blue-700 transition"
          >
            Logg inn
          </button>
        </div>
        <div className="mt-8 md:mt-0 md:ml-8">
          <img src="/del1.png" alt="Liv boks" className="w-64 h-auto" />
        </div>
      </section>

      {/* Del 2: Ikoner */}
      <section className="flex justify-center gap-12 py-12 bg-gray-50">
        <img src="/del2-ikoner1.png" alt="Ikoner for funksjoner" className="h-24 w-auto" />
      </section>

      {/* Del 3: Bunn */}
      <footer className="mt-auto">
        <img src="/del3.png" alt="Bunn grafikk" className="w-full" />
      </footer>
    </div>
  );
};

const root = createRoot(document.getElementById("root"));
root.render(<App />);
