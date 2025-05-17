// /api/config.js på Vercel
export default function handler(req, res) {
  res.status(200).json({
    openai_api_key: process.env.APINOKKEL_OPENAI,
  });
}
