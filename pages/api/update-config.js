// pages/api/update-config.js
import fs from "fs";
import path from "path";

export default function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ message: "Method not allowed" });
  }

  const { system_prompt, speak_text } = req.body;

  if (typeof system_prompt !== "string" || typeof speak_text !== "string") {
    return res.status(400).json({ message: "Invalid input" });
  }

  const filePath = path.join(process.cwd(), "public", "config.json");

  try {
    fs.writeFileSync(
      filePath,
      JSON.stringify({ system_prompt, speak_text }, null, 2),
      "utf-8"
    );
    res.status(200).json({ message: "Config updated" });
  } catch (err) {
    console.error("Error writing config file:", err);
    res.status(500).json({ message: "Failed to update config" });
  }
}
