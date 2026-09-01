const CONFIG_PATH = "public/config.json";

export function githubSettings() {
  const repository = process.env.GH_REPO || process.env.GITHUB_REPOSITORY || "anderswr/chatbox-config";
  const owner = process.env.GH_USERNAME;
  const fullName = repository.includes("/") ? repository : `${owner || "anderswr"}/${repository}`;
  return {
    fullName,
    branch: process.env.GH_BRANCH || "main",
    token: process.env.GH_TOKEN || process.env.GITHUB_TOKEN || "",
    path: CONFIG_PATH,
  };
}

export function githubHeaders(token = "") {
  return {
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export function contentsUrl({ fullName, path, branch }) {
  return `https://api.github.com/repos/${fullName}/contents/${path}?ref=${encodeURIComponent(branch)}`;
}

